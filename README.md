# WRF Namelist.wps Interactive Configuration Tool
## Description

This Python script, `WRF_Namelist.wps_Interactive_Configuration_Tool.py`, is designed to interactively generate a `namelist.wps` file for the Weather Research and Forecasting (WRF) Pre-Processing System (WPS). It guides users through the configuration process by prompting for necessary parameters for each section of the `namelist.wps` file: `&share`, `&geogrid`, `&ungrib`, and `&metgrid`.

The script aims to simplify the often complex task of manually creating or editing `namelist.wps` by providing:

* **Interactive prompts**: User-friendly questions to guide configuration.
* **Default values**: Sensible default settings are provided and can be accepted by simply pressing Enter.
* **Input validation**: Basic input validation is performed to ensure correct data types and formats.
* **Existing namelist support**: Option to load settings from an existing `namelist.wps` file to use as a starting point or for modification.
* **Nested domain configuration**:  Assistance with setting up nested domains, including suggesting parent IDs, grid ratios, and starting positions.
* **Configuration review**: A summary of the configured settings is presented before writing the `namelist.wps` file, allowing for final confirmation.

## Features

* **Interactive Configuration**: Step-by-step prompts for each parameter in `namelist.wps`.
* **Default Values**: Pre-populated default values for quick setup.
* **Input Validation**: Ensures valid input types (integers, floats, dates, options).
* **Load Existing Namelist**: Option to use an existing `namelist.wps` as a template.
* **Nested Domain Support**:  Guides configuration for single and multiple (nested) domains.
* **Domain Nesting Suggestions**: Provides suggested starting positions for nested domains based on parent domain dimensions and grid ratios.
* **Geographic Data Resolution Options**: Lists common options for geographic data resolution.
* **Configuration Review**: Summarizes all settings before writing the output file.
* **User-Friendly**: Designed for users who may be new to WRF or WPS configuration.

## Requirements

* **Python 3**:  The script is written in Python 3. Ensure you have Python 3 installed on your system.
* **No external Python libraries are required.** The script uses only built-in Python modules.

## Usage

1. **Download the script**: Download `WRF_Namelist.wps_Interactive_Configuration_Tool.py` to your WPS directory (the directory where you would normally run `geogrid.exe`, `ungrib.exe`, and `metgrid.exe`).

2. **Make the script executable (optional)**:  If you want to run the script directly using `./WRF_Namelist.wps_Interactive_Configuration_Tool.py`, you may need to make it executable:
   ```bash
   chmod +x WRF_Namelist.wps_Interactive_Configuration_Tool.py
   ```

3. **Run the script**: Execute the script from your terminal within the WPS directory:
   ```bash
   ./WRF_Namelist.wps_Interactive_Configuration_Tool.py
   ```
   or
   ```bash
   python WRF_Namelist.wps_Interactive_Configuration_Tool.py
   ```

4. **Follow the prompts**: The script will guide you through each section of the `namelist.wps` file.
    * **Accept defaults**: Press **Enter** to accept the default value shown in brackets `[brackets]`.
    * **Enter custom values**: Type your desired value and press **Enter**.
    * **Quit**: Type `q` at any prompt and press **Enter** to quit the configuration process.

5. **Review and confirm**: After configuring all sections, the script will display a summary of your settings. Review them carefully and confirm if they are correct.

6. **Output file**: If you confirm the configuration, the script will write the `namelist.wps` file. You will be prompted to provide an output filename (default is `namelist.wps`).

## Configuration Sections

The script configures the following sections of the `namelist.wps` file:

* **`&share`**: General settings for WRF domains, including:
    * `wrf_core` (ARW or NMM core)
    * `max_dom` (number of domains)
    * `start_date`, `end_date` (simulation start and end times for each domain)
    * `interval_seconds` (interval between input meteorological data)
    * `io_form_geogrid` (I/O format for geogrid output)
    * `debug_level` (verbosity of output)

* **`&geogrid`**: Domain definitions and geographic data settings, including:
    * `parent_id`, `parent_grid_ratio`, `i_parent_start`, `j_parent_start` (nesting parameters)
    * `e_we`, `e_sn` (domain dimensions in grid points)
    * `geog_data_res` (geographic data resolution)
    * `dx`, `dy` (grid spacing for the coarse domain)
    * `map_proj` (map projection type)
    * `ref_lat`, `ref_lon`, `truelat1`, `truelat2`, `stand_lon` (projection parameters)
    * `geog_data_path` (path to geographic data directory)

* **`&ungrib`**: Settings for extracting meteorological data from GRIB files, including:
    * `out_format` (output format for intermediate files - usually WPS)
    * `prefix` (prefix for intermediate files)

* **`&metgrid`**: Settings for interpolating meteorological data to the model grid, including:
    * `fg_name` (prefix(es) of the intermediate files generated by ungrib)
    * `io_form_metgrid` (I/O format for metgrid output)

## Output

The script generates a `namelist.wps` file in the current directory (or the filename you specify). This file is ready to be used with the WPS programs (`geogrid.exe`, `ungrib.exe`, `metgrid.exe`).

## Notes

* **Interactive Script**: This is an interactive script. It requires user input to configure the `namelist.wps` file.
* **Existing Namelist**: If a `namelist.wps` file already exists in the directory, the script will ask if you want to use it for default values. This can be helpful for modifying an existing configuration.
* **Error Handling**: The script includes basic error handling for invalid input and file operations, but it's always recommended to review the generated `namelist.wps` file to ensure it meets your specific requirements.
* **Geographic Data Path**:  Make sure to set the `geog_data_path` in the `&geogrid` section to the correct path where your WRF geographic data is located.
* **Domain Nesting**: When configuring nested domains, pay attention to the suggested starting positions and domain dimensions to ensure proper nesting within the parent domain.
* **Experimentation**:  WRF configuration can be complex. Don't hesitate to experiment with different settings to understand their impact on your simulations. Always consult the WRF documentation for detailed information on each parameter.
