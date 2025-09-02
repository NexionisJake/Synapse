import netCDF4
from datetime import datetime
import numpy as np

def read_argo_metadata(filepath):
    """
    Reads and prints metadata from an Argo float .nc file in a human-readable format.

    Args:
        filepath (str): The path to the .nc file.
    """
    try:
        with netCDF4.Dataset(filepath, 'r') as nc_file:
            print("="*60)
            print(f"Reading Argo Float Metadata from: {filepath}")
            print("="*60)

            # --- Global Attributes (General Information) ---
            print("\n--- General Information ---\n")
            global_attrs = nc_file.ncattrs()
            for attr in global_attrs:
                value = nc_file.getncattr(attr)
                if isinstance(value, bytes):
                    value = value.decode('utf-8', 'ignore')
                print(f"{attr.replace('_', ' ').title()}: {value}")

            # --- Platform Information ---
            print("\n--- Platform Details ---\n")
            platform_info_vars = [
                'PLATFORM_NUMBER', 'PLATFORM_TYPE', 'PLATFORM_MAKER',
                'FLOAT_SERIAL_NO', 'WMO_INST_TYPE', 'PROJECT_NAME',
                'PI_NAME', 'FLOAT_OWNER', 'OPERATING_INSTITUTION'
            ]
            for var_name in platform_info_vars:
                if var_name in nc_file.variables:
                    var = nc_file.variables[var_name]
                    # The chartostring function handles conversion from char arrays.
                    # We just need to strip whitespace from the final string(s).
                    data = netCDF4.chartostring(var[:])
                    if isinstance(data, np.ndarray):
                        if data.ndim == 0:
                            data_str = str(data).strip()
                        else:
                            data_str = ', '.join(s.strip() for s in data)
                    else:
                        data_str = data.strip()
                    if data_str:
                        description = var.long_name if 'long_name' in var.ncattrs() else var_name.replace('_', ' ').title()
                        print(f"{description}: {data_str}")

            # --- Deployment Information ---
            print("\n--- Deployment Details ---\n")
            deployment_vars = {
                'LAUNCH_DATE': 'Launch Date',
                'LAUNCH_LATITUDE': 'Launch Latitude',
                'LAUNCH_LONGITUDE': 'Launch Longitude',
                'DEPLOYMENT_PLATFORM': 'Deployment Platform',
                'DEPLOYMENT_CRUISE_ID': 'Deployment Cruise ID'
            }
            for var_name, description in deployment_vars.items():
                if var_name in nc_file.variables:
                    var = nc_file.variables[var_name]
                    if var.size > 0: # Check if there is any data
                        # For text-based fields (dtype 'S1' indicates character array)
                        if 'S' in str(var.dtype):
                             data = netCDF4.chartostring(var[:])
                             if isinstance(data, np.ndarray):
                                 if data.ndim == 0:
                                     value_str = str(data).strip()
                                 else:
                                     value_str = ', '.join(s.strip() for s in data)
                             else:
                                 value_str = data.strip()
                             if value_str:
                                if 'date' in var_name.lower():
                                    try:
                                        dt_object = datetime.strptime(value_str, '%Y%m%d%H%M%S')
                                        print(f"{description}: {dt_object.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                                    except ValueError:
                                        print(f"{description}: {value_str} (Could not parse date)")
                                else:
                                    print(f"{description}: {value_str}")
                        # For numeric fields
                        else:
                            value = var[0]
                            print(f"{description}: {value}")


            # --- Configuration Parameters ---
            print("\n--- Launch Configuration ---\n")
            if 'LAUNCH_CONFIG_PARAMETER_NAME' in nc_file.variables and 'LAUNCH_CONFIG_PARAMETER_VALUE' in nc_file.variables:
                param_names = netCDF4.chartostring(nc_file.variables['LAUNCH_CONFIG_PARAMETER_NAME'][:])
                param_values = nc_file.variables['LAUNCH_CONFIG_PARAMETER_VALUE'][:]

                for name, value in zip(param_names, param_values):
                    clean_name = name.strip()
                    if clean_name and not (hasattr(value, 'mask') and not np.all(value.mask)):
                        print(f"{clean_name}: {value}")

            # --- Sensor Information ---
            print("\n--- Sensor Details ---\n")
            if 'PARAMETER' in nc_file.variables:
                params = netCDF4.chartostring(nc_file.variables['PARAMETER'][:])
                sensors = netCDF4.chartostring(nc_file.variables['PARAMETER_SENSOR'][:])
                units = netCDF4.chartostring(nc_file.variables['PARAMETER_UNITS'][:])
                accuracies = nc_file.variables['PARAMETER_ACCURACY'][:]
                resolutions = nc_file.variables['PARAMETER_RESOLUTION'][:]

                for i, param in enumerate(params):
                    param_clean = param.strip()
                    if param_clean:
                        print(f"Parameter: {param_clean}")
                        if i < len(sensors) and sensors[i].strip():
                            print(f"  - Measured by: {sensors[i].strip()}")
                        if i < len(units) and units[i].strip():
                            print(f"  - Units: {units[i].strip()}")
                        if i < len(accuracies) and hasattr(accuracies, 'mask') and not np.all(accuracies.mask[i]):
                            print(f"  - Accuracy: {accuracies[i]}")
                        if i < len(resolutions) and hasattr(resolutions, 'mask') and not np.all(resolutions.mask[i]):
                            print(f"  - Resolution: {resolutions[i]}")
                        print("-" * 20)

    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    file_to_read = '/home/nexion/Desktop/SIH/raw data/1902670_meta.nc'
    read_argo_metadata(file_to_read) 
