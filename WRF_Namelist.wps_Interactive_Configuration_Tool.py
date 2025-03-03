#!/usr/bin/env python3

import os
import datetime
import sys
import math

def main():
    print("WRF Namelist.wps Interactive Configuration Tool")
    print("==============================================")
    print("This script will help you configure your namelist.wps file for WRF.")
    print("Press Enter to accept default values shown in [brackets].")
    print("Type 'q' at any prompt to quit.")
    print()
    
    # Initialize with default values
    share_params = default_share_params()
    geogrid_params = default_geogrid_params()
    ungrib_params = default_ungrib_params()
    metgrid_params = default_metgrid_params()
    
    # Check if existing namelist.wps should be used for defaults
    if os.path.exists("namelist.wps"):
        use_existing = get_input("An existing namelist.wps file was found. Use it for defaults? (y/n)", "y")
        if use_existing.lower() in ['y', 'yes']:
            try:
                share_params, geogrid_params, ungrib_params, metgrid_params = read_existing_namelist("namelist.wps")
                print("Successfully read existing namelist.wps for defaults.")
            except Exception as e:
                print(f"Error reading existing namelist.wps: {e}")
                print("Using built-in defaults instead.")
    
    # Configure each section
    share_params = configure_share(share_params)
    
    # Update geogrid_params max_dom based on share_params
    max_dom = share_params["max_dom"]
    geogrid_params = adjust_params_for_max_dom(geogrid_params, max_dom)
    geogrid_params = configure_geogrid(geogrid_params, max_dom)
    
    ungrib_params = configure_ungrib(ungrib_params)
    metgrid_params = configure_metgrid(metgrid_params)
    
    # Review settings before writing
    if review_configuration(share_params, geogrid_params, ungrib_params, metgrid_params):
        # Write the namelist.wps file
        output_file = get_input("Output filename", "namelist.wps")
        write_namelist_wps(output_file, share_params, geogrid_params, ungrib_params, metgrid_params)
        
        print(f"\nConfiguration complete! Namelist.wps has been written to {output_file}")
    else:
        print("\nConfiguration canceled. Exiting without writing file.")

def default_share_params():
    # Current date for defaults
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    
    return {
        "wrf_core": "ARW",
        "max_dom": 1,
        "start_date": [now.strftime("%Y-%m-%d_%H:%M:%S")],
        "end_date": [tomorrow.strftime("%Y-%m-%d_%H:%M:%S")],
        "interval_seconds": 21600,
        "io_form_geogrid": 2,
        "debug_level": 0
    }

def default_geogrid_params():
    return {
        "parent_id": [1],
        "parent_grid_ratio": [1],
        "i_parent_start": [1],
        "j_parent_start": [1],
        "e_we": [100],
        "e_sn": [100],
        "geog_data_res": ["default"],
        "dx": 30000,
        "dy": 30000,
        "map_proj": "lambert",
        "ref_lat": 34.0,
        "ref_lon": -81.0,
        "truelat1": 30.0,
        "truelat2": 60.0,
        "stand_lon": -81.0,
        "geog_data_path": "/path/to/geog"
    }

def default_ungrib_params():
    return {
        "out_format": "WPS",
        "prefix": "FILE"
    }

def default_metgrid_params():
    return {
        "fg_name": ["FILE"],
        "io_form_metgrid": 2
    }

def adjust_params_for_max_dom(params, max_dom):
    """Adjust list parameters to match max_dom"""
    list_params = [
        "parent_id", "parent_grid_ratio", "i_parent_start", 
        "j_parent_start", "e_we", "e_sn", "geog_data_res"
    ]
    
    for key in list_params:
        if key not in params:
            continue
            
        # Extend the list if needed
        while len(params[key]) < max_dom:
            if key == "parent_id" and len(params[key]) > 0:
                # For nested domains, parent is usually the domain one level up
                params[key].append(len(params[key]))
            elif key == "parent_grid_ratio" and len(params[key]) > 0:
                if len(params[key]) == 1:
                    # First nested domain often has ratio 3
                    params[key].append(3)
                else:
                    # Subsequent domains often keep the same ratio
                    params[key].append(params[key][-1])
            elif key in ["i_parent_start", "j_parent_start"]:
                # Default to center of parent domain for nested domains
                if key == "i_parent_start" and len(params[key]) > 0 and len(params["e_we"]) > len(params[key]):
                    parent_idx = params["parent_id"][len(params[key])] - 1
                    center = params["e_we"][parent_idx] // 2
                    child_size = params["e_we"][len(params[key])-1] // params["parent_grid_ratio"][len(params[key])-1]
                    params[key].append(max(1, center - child_size // 2))
                elif key == "j_parent_start" and len(params[key]) > 0 and len(params["e_sn"]) > len(params[key]):
                    parent_idx = params["parent_id"][len(params[key])] - 1
                    center = params["e_sn"][parent_idx] // 2
                    child_size = params["e_sn"][len(params[key])-1] // params["parent_grid_ratio"][len(params[key])-1]
                    params[key].append(max(1, center - child_size // 2))
                else:
                    params[key].append(1)
            elif key in ["e_we", "e_sn"]:
                # Nested domains often have similar dimensions to parent
                if len(params[key]) > 0:
                    # Make sure dimensions are odd for nesting
                    last_val = params[key][-1]
                    if last_val % 2 == 0:
                        last_val += 1
                    params[key].append(last_val)
                else:
                    params[key].append(100)  # Default
            elif key == "geog_data_res":
                # Use same resolution as parent by default
                if len(params[key]) > 0:
                    params[key].append(params[key][-1])
                else:
                    params[key].append("default")
        
        # Trim if too long
        params[key] = params[key][:max_dom]
    
    return params

def read_existing_namelist(filename):
    """Read an existing namelist.wps file and extract parameters."""
    
    share_params = {}
    geogrid_params = {}
    ungrib_params = {}
    metgrid_params = {}
    
    current_section = None
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("!"):
                continue
            
            # Check for section start
            if line.startswith("&"):
                section_name = line[1:].lower()
                if section_name == "share":
                    current_section = share_params
                elif section_name == "geogrid":
                    current_section = geogrid_params
                elif section_name == "ungrib":
                    current_section = ungrib_params
                elif section_name == "metgrid":
                    current_section = metgrid_params
                continue
            
            # Check for section end
            if line == "/" or line.startswith("/"):
                current_section = None
                continue
            
            # Parse parameter if we're in a section
            if current_section is not None:
                # Split at equals sign
                parts = line.split("=", 1)
                if len(parts) != 2:
                    continue
                
                param_name = parts[0].strip()
                param_value = parts[1].strip()
                
                # Remove trailing comma if present
                if param_value.endswith(","):
                    param_value = param_value[:-1]
                
                # Handle arrays (comma-separated values)
                if "," in param_value:
                    values = [v.strip() for v in param_value.split(",")]
                    
                    # Convert to appropriate type
                    processed_values = []
                    for v in values:
                        # Remove quotes for strings
                        if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
                            processed_values.append(v[1:-1])
                        # Try to convert to number if possible
                        else:
                            try:
                                if "." in v:
                                    processed_values.append(float(v))
                                else:
                                    processed_values.append(int(v))
                            except ValueError:
                                processed_values.append(v)
                    
                    current_section[param_name] = processed_values
                else:
                    # Single value
                    if (param_value.startswith("'") and param_value.endswith("'")) or \
                       (param_value.startswith('"') and param_value.endswith('"')):
                        current_section[param_name] = param_value[1:-1]
                    else:
                        try:
                            if "." in param_value:
                                current_section[param_name] = float(param_value)
                            else:
                                current_section[param_name] = int(param_value)
                        except ValueError:
                            current_section[param_name] = param_value
    
    # Convert any single-item lists to match default format
    for params in [share_params, geogrid_params, ungrib_params, metgrid_params]:
        for key, value in params.items():
            if key in ["start_date", "end_date", "parent_id", "parent_grid_ratio", 
                       "i_parent_start", "j_parent_start", "e_we", "e_sn", "geog_data_res",
                       "fg_name"] and not isinstance(value, list):
                params[key] = [value]
    
    return share_params, geogrid_params, ungrib_params, metgrid_params

def get_input(prompt, default=None, validator=None):
    """
    Get user input with a default value and optional validation.
    """
    while True:
        if default is not None:
            user_input = input(f"{prompt} [{default}]: ")
            if not user_input:
                return default
        else:
            user_input = input(f"{prompt}: ")
        
        # Check for quit command
        if user_input.lower() == 'q':
            print("Configuration canceled by user.")
            sys.exit(0)
        
        if validator:
            is_valid, error_message = validator(user_input)
            if not is_valid:
                print(f"Error: {error_message}")
                continue
        
        return user_input

def validate_date(date_str):
    """Validate that a string is in YYYY-MM-DD_HH:MM:SS format."""
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d_%H:%M:%S")
        return True, ""
    except ValueError:
        return False, "Date must be in format YYYY-MM-DD_HH:MM:SS"

def validate_integer(value):
    """Validate that a string can be converted to an integer."""
    try:
        int(value)
        return True, ""
    except ValueError:
        return False, "Value must be an integer"

def validate_positive_integer(value):
    """Validate that a string can be converted to a positive integer."""
    try:
        intval = int(value)
        if intval <= 0:
            return False, "Value must be a positive integer"
        return True, ""
    except ValueError:
        return False, "Value must be an integer"

def validate_float(value):
    """Validate that a string can be converted to a float."""
    try:
        float(value)
        return True, ""
    except ValueError:
        return False, "Value must be a number"

def validate_option(value, options):
    """Validate that a string is one of the allowed options."""
    if value in options:
        return True, ""
    return False, f"Value must be one of: {', '.join(options)}"

def suggest_nest_location(parent_dim, nest_dim, ratio):
    """Suggest a good starting position for a nested domain"""
    # Center the nest in the parent domain
    parent_center = parent_dim // 2
    nest_size_in_parent = math.ceil(nest_dim / ratio)
    start_pos = max(1, parent_center - nest_size_in_parent // 2)
    return start_pos

def configure_share(params):
    print("\n=== Share Section Configuration ===")
    print("This section contains general settings for the WRF domain.\n")
    
    # WRF core
    params["wrf_core"] = get_input(
        "WRF core (ARW/NMM) - Advanced Research WRF or Non-hydrostatic Mesoscale Model", 
        params["wrf_core"],
        lambda x: validate_option(x, ["ARW", "NMM"])
    )
    
    # Max domains
    max_dom_str = get_input(
        "Maximum number of domains (1 for single domain, >1 for nested domains)", 
        str(params["max_dom"]),
        validate_positive_integer
    )
    params["max_dom"] = int(max_dom_str)
    
    # Adjust lists based on max_dom
    for key in ["start_date", "end_date"]:
        while len(params[key]) < params["max_dom"]:
            params[key].append(params[key][0])
        params[key] = params[key][:params["max_dom"]]
    
    # Start dates for each domain
    print("\nEnter start date for each domain (YYYY-MM-DD_HH:MM:SS):")
    for i in range(params["max_dom"]):
        params["start_date"][i] = get_input(
            f"  Domain {i+1} start date",
            params["start_date"][i],
            validate_date
        )
    
    # End dates for each domain
    print("\nEnter end date for each domain (YYYY-MM-DD_HH:MM:SS):")
    for i in range(params["max_dom"]):
        params["end_date"][i] = get_input(
            f"  Domain {i+1} end date",
            params["end_date"][i],
            validate_date
        )
    
    # Interval seconds
    interval_str = get_input(
        "Interval between input meteorological files (seconds)",
        str(params["interval_seconds"]),
        validate_positive_integer
    )
    params["interval_seconds"] = int(interval_str)
    
    # IO form geogrid
    io_form_str = get_input(
        "I/O format for geogrid (1=binary, 2=netCDF, 3=GRIB1)",
        str(params["io_form_geogrid"]),
        lambda x: validate_option(x, ["1", "2", "3"])
    )
    params["io_form_geogrid"] = int(io_form_str)
    
    # Debug level
    debug_str = get_input(
        "Debug level (0-1000, higher = more debug output)",
        str(params["debug_level"]),
        validate_integer
    )
    params["debug_level"] = int(debug_str)
    
    return params

def configure_geogrid(params, max_dom):
    print("\n=== Geogrid Section Configuration ===")
    print("This section defines the model domains and geographical data.\n")
    
    # Map projection
    params["map_proj"] = get_input(
        "Map projection (lambert/mercator/polar/lat-lon)",
        params["map_proj"],
        lambda x: validate_option(x, ["lambert", "mercator", "polar", "lat-lon"])
    )
    
    # Grid spacings for coarse domain
    dx_str = get_input(
        "Grid spacing in x-direction for coarse domain (meters)",
        str(params["dx"]),
        validate_positive_integer
    )
    params["dx"] = float(dx_str)
    
    dy_str = get_input(
        "Grid spacing in y-direction for coarse domain (meters)",
        str(params["dy"]),
        validate_positive_integer
    )
    params["dy"] = float(dy_str)
    
    # Reference lat/lon
    ref_lat_str = get_input(
        "Reference latitude (degrees) - center of coarse domain",
        str(params["ref_lat"]),
        validate_float
    )
    params["ref_lat"] = float(ref_lat_str)
    
    ref_lon_str = get_input(
        "Reference longitude (degrees) - center of coarse domain",
        str(params["ref_lon"]),
        validate_float
    )
    params["ref_lon"] = float(ref_lon_str)
    
    # Parameters specific to projection type
    if params["map_proj"] == "lambert":
        print("\nLambert projection requires true latitudes:")
        truelat1_str = get_input(
            "  True latitude 1 (degrees)",
            str(params["truelat1"]),
            validate_float
        )
        params["truelat1"] = float(truelat1_str)
        
        truelat2_str = get_input(
            "  True latitude 2 (degrees)",
            str(params["truelat2"]),
            validate_float
        )
        params["truelat2"] = float(truelat2_str)
    
    elif params["map_proj"] == "mercator":
        truelat1_str = get_input(
            "True latitude (degrees)",
            str(params.get("truelat1", 0.0)),
            validate_float
        )
        params["truelat1"] = float(truelat1_str)
    
    elif params["map_proj"] == "polar":
        truelat1_str = get_input(
            "True latitude (degrees)",
            str(params.get("truelat1", 90.0)),
            validate_float
        )
        params["truelat1"] = float(truelat1_str)
    
    # Standard longitude
    stand_lon_str = get_input(
        "Standard longitude (degrees) - usually same as ref_lon",
        str(params["stand_lon"]),
        validate_float
    )
    params["stand_lon"] = float(stand_lon_str)
    
    # Configure domain nesting if needed
    if max_dom > 1:
        print("\nSetting up domain nesting:")
        
        # Configure parent IDs and grid ratios first
        for i in range(max_dom):
            if i == 0:
                params["parent_id"][i] = 1  # First domain always has parent_id=1
            else:
                parent_id_str = get_input(
                    f"  Domain {i+1} parent ID (usually {i})",
                    str(params["parent_id"][i]),
                    lambda x: validate_option(x, [str(j) for j in range(1, i+1)])
                )
                params["parent_id"][i] = int(parent_id_str)
        
        for i in range(max_dom):
            if i == 0:
                params["parent_grid_ratio"][i] = 1  # First domain always has ratio=1
            else:
                ratio_str = get_input(
                    f"  Domain {i+1} parent grid ratio (typically 3 or 5)",
                    str(params["parent_grid_ratio"][i]),
                    validate_positive_integer
                )
                params["parent_grid_ratio"][i] = int(ratio_str)
    
    # Domain dimensions
    print("\nConfiguring domain dimensions:")
    for i in range(max_dom):
        if i == 0:
            print(f"\n  Domain 1 (coarse domain) dimensions:")
        else:
            print(f"\n  Domain {i+1} (nested domain) dimensions:")
            parent_index = params["parent_id"][i] - 1
            
            # Suggest dimensions for nested domains
            suggested_e_we = params["e_we"][parent_index] // 3
            if suggested_e_we % 2 == 0:
                suggested_e_we += 1  # Make it odd for better nesting
            
            suggested_e_sn = params["e_sn"][parent_index] // 3
            if suggested_e_sn % 2 == 0:
                suggested_e_sn += 1  # Make it odd for better nesting
            
            print(f"    Parent domain dimensions: {params['e_we'][parent_index]} x {params['e_sn'][parent_index]}")
            print(f"    Suggested dimensions: {suggested_e_we} x {suggested_e_sn}")
        
        # Get dimensions for this domain
        e_we_str = get_input(
            f"    West-east dimension (grid points)",
            str(params["e_we"][i]) if i < len(params["e_we"]) else str(101),
            validate_positive_integer
        )
        params["e_we"][i] = int(e_we_str)
        
        e_sn_str = get_input(
            f"    South-north dimension (grid points)",
            str(params["e_sn"][i]) if i < len(params["e_sn"]) else str(101),
            validate_positive_integer
        )
        params["e_sn"][i] = int(e_sn_str)
    
    # Configure i_parent_start and j_parent_start for nested domains
    if max_dom > 1:
        print("\nSetting starting positions of nested domains within parent domains:")
        for i in range(1, max_dom):  # Skip the first domain
            parent_index = params["parent_id"][i] - 1
            
            # Suggest good starting locations for nested domains
            suggested_i = suggest_nest_location(
                params["e_we"][parent_index], 
                params["e_we"][i], 
                params["parent_grid_ratio"][i]
            )
            
            suggested_j = suggest_nest_location(
                params["e_sn"][parent_index], 
                params["e_sn"][i], 
                params["parent_grid_ratio"][i]
            )
            
            print(f"\n  Domain {i+1} parent is Domain {parent_index+1}")
            print(f"  Parent dimensions: {params['e_we'][parent_index]} x {params['e_sn'][parent_index]}")
            print(f"  Nest dimensions: {params['e_we'][i]} x {params['e_sn'][i]}")
            print(f"  Suggested starting position: ({suggested_i}, {suggested_j})")
            
            i_start_str = get_input(
                f"    i_parent_start (west-east position in parent)",
                str(suggested_i),
                validate_positive_integer
            )
            params["i_parent_start"][i] = int(i_start_str)
            
            j_start_str = get_input(
                f"    j_parent_start (south-north position in parent)",
                str(suggested_j),
                validate_positive_integer
            )
            params["j_parent_start"][i] = int(j_start_str)
            
            # Check if the nested domain fits within the parent
            i_end = params["i_parent_start"][i] + math.ceil(params["e_we"][i] / params["parent_grid_ratio"][i]) - 1
            j_end = params["j_parent_start"][i] + math.ceil(params["e_sn"][i] / params["parent_grid_ratio"][i]) - 1
            
            if i_end > params["e_we"][parent_index] or j_end > params["e_sn"][parent_index]:
                print("  WARNING: The nested domain extends beyond the parent domain boundaries.")
                print(f"  Nested domain ends at ({i_end}, {j_end}) in parent coordinates.")
                print(f"  Parent domain has dimensions {params['e_we'][parent_index]} x {params['e_sn'][parent_index]}")
                
                adjust = get_input("  Adjust the nested domain to fit? (y/n)", "y")
                if adjust.lower() in ['y', 'yes']:
                    if i_end > params["e_we"][parent_index]:
                        new_i_start = max(1, params["e_we"][parent_index] - math.ceil(params["e_we"][i] / params["parent_grid_ratio"][i]) + 1)
                        params["i_parent_start"][i] = new_i_start
                    
                    if j_end > params["e_sn"][parent_index]:
                        new_j_start = max(1, params["e_sn"][parent_index] - math.ceil(params["e_sn"][i] / params["parent_grid_ratio"][i]) + 1)
                        params["j_parent_start"][i] = new_j_start
                    
                    print(f"  Adjusted starting position to ({params['i_parent_start'][i]}, {params['j_parent_start'][i]})")
    
    # Geographic data resolution
    print("\nConfiguring geographical data resolution:")
    print("(Options: 'default', 'modis_30s', 'modis_15s', 'usgs_30s', 'usgs_15s', 'usgs_5m', 'usgs_2m', etc.)")
    
    for i in range(max_dom):
        # Suggest progressively higher resolutions for nested domains
        suggested_res = "default"
        if i == 0:
            suggested_res = "modis_30s"
        elif i == 1:
            suggested_res = "modis_15s"
        elif i >= 2:
            suggested_res = "modis_15s"
        
        params["geog_data_res"][i] = get_input(
            f"  Domain {i+1} geographical data resolution",
            params["geog_data_res"][i] if i < len(params["geog_data_res"]) else suggested_res
        )
    
    # Geog data path
    params["geog_data_path"] = get_input(
        "Path to geographic data directory",
        params["geog_data_path"]
    )
    
    return params

def configure_ungrib(params):
    print("\n=== Ungrib Section Configuration ===")
    print("This section configures how to extract meteorological data from GRIB files.\n")
    
    # Output format
    params["out_format"] = get_input(
        "Output format (WPS/SI/MM5/WRF)",
        params["out_format"],
        lambda x: validate_option(x, ["WPS", "SI", "MM5", "WRF"])
    )
    
    # Prefix
    params["prefix"] = get_input(
        "Prefix for intermediate files (used as input to metgrid)",
        params["prefix"]
    )
    
    return params

def configure_metgrid(params):
    print("\n=== Metgrid Section Configuration ===")
    print("This section configures how to interpolate meteorological data to the model grid.\n")
    
    # fg_name (file name prefix)
    fg_name = get_input(
        "File name prefix for ungribbed data (separate multiple with commas)",
        ",".join(params["fg_name"])
    )
    params["fg_name"] = [s.strip() for s in fg_name.split(",")]
    
    # IO form metgrid
    io_form_str = get_input(
        "I/O format for metgrid (1=binary, 2=netCDF, 3=GRIB1)",
        str(params["io_form_metgrid"]),
        lambda x: validate_option(x, ["1", "2", "3"])
    )
    params["io_form_metgrid"] = int(io_form_str)
    
    return params

def review_configuration(share, geogrid, ungrib, metgrid):
    """Show a summary of the configuration and ask for confirmation"""
    print("\n=== Review Configuration ===")
    
    print("\nShare section:")
    print(f"  WRF Core: {share['wrf_core']}")
    print(f"  Number of domains: {share['max_dom']}")
    print(f"  Start date: {share['start_date'][0]} (domain 1)")
    print(f"  End date: {share['end_date'][0]} (domain 1)")
    print(f"  Interval between met. data: {share['interval_seconds']} seconds")
    
    print("\nGeogrid section:")
    print(f"  Map projection: {geogrid['map_proj']}")
    print(f"  Reference point: ({geogrid['ref_lat']}, {geogrid['ref_lon']})")
    print(f"  Grid spacing: {geogrid['dx']} x {geogrid['dy']} meters (domain 1)")
    
    for i in range(share['max_dom']):
        print(f"\n  Domain {i+1} configuration:")
        print(f"    Grid dimensions: {geogrid['e_we'][i]} x {geogrid['e_sn'][i]} points")
        
        if i > 0:
            parent_id = geogrid['parent_id'][i]
            ratio = geogrid['parent_grid_ratio'][i]
            i_start = geogrid['i_parent_start'][i]
            j_start = geogrid['j_parent_start'][i]
            print(f"    Parent: Domain {parent_id}")
            print(f"    Refinement ratio: {ratio}:1")
            print(f"    Starting position in parent: ({i_start}, {j_start})")
            
            # Calculate the actual resolution of this domain
            parent_idx = parent_id - 1
            domain_dx = geogrid['dx'] / (geogrid['parent_grid_ratio'][i] * 
                                      (1 if parent_idx == 0 else geogrid['parent_grid_ratio'][parent_idx]))
            domain_dy = geogrid['dy'] / (geogrid['parent_grid_ratio'][i] * 
                                      (1 if parent_idx == 0 else geogrid['parent_grid_ratio'][parent_idx]))
            print(f"    Grid spacing: {domain_dx:.1f} x {domain_dy:.1f} meters")
        
        print(f"    Geographic data resolution: {geogrid['geog_data_res'][i]}")
    
    print("\nUngrib section:")
    print(f"  Output format: {ungrib['out_format']}")
    print(f"  File prefix: {ungrib['prefix']}")
    
    print("\nMetgrid section:")
    print(f"  Input file prefixes: {', '.join(metgrid['fg_name'])}")
    print(f"  I/O format: {metgrid['io_form_metgrid']}")
    
    # Ask for confirmation
    confirm = get_input("\nIs this configuration correct? (y/n)", "y")
    return confirm.lower() in ['y', 'yes']

def write_namelist_wps(filename, share, geogrid, ungrib, metgrid):
    """Write the parameters to the namelist.wps file."""
    
    # Helper function to format arrays correctly
    def format_value(value):
        if isinstance(value, list):
            # Format lists with commas
            if all(isinstance(x, str) for x in value):
                return ", ".join(f"'{x}'" for x in value)
            else:
                return ", ".join(str(x) for x in value)
        elif isinstance(value, str):
            return f"'{value}'"
        else:
            return str(value)
    
    try:
        with open(filename, 'w') as f:
            # Write share section
            f.write("&share\n")
            for key, value in share.items():
                f.write(f" {key} = {format_value(value)},\n")
            f.write("/\n\n")
            
            # Write geogrid section
            f.write("&geogrid\n")
            for key, value in geogrid.items():
                f.write(f" {key} = {format_value(value)},\n")
            f.write("/\n\n")
            
            # Write ungrib section
            f.write("&ungrib\n")
            for key, value in ungrib.items():
                f.write(f" {key} = {format_value(value)},\n")
            f.write("/\n\n")
            
            # Write metgrid section
            f.write("&metgrid\n")
            for key, value in metgrid.items():
                f.write(f" {key} = {format_value(value)},\n")
            f.write("/\n")
    except Exception as e:
        print(f"Error writing to {filename}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting.")
        sys.exit(1)