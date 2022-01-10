# SARveillance
Sentinel-1 SAR time series analysis for OSINT use. 

## Description 

Generates a time lapse GIF of the Sentinel-1 satellite images for the location and date range specified.

## Getting Started

### Requirements

- **Python 3.9** 
- **conda**: The installation script that installs the dependencies needs to use both conda and pip to fetch the required dependencies, so please use conda and create a new conda virtual environment.

### Installing Packages

```shell
bash install_requirements.sh
```

## To Run

Running the `main.py` script will generate the time lapse GIF for the location and date range specified.

```shell
python main.py selected_base_name selected_start_date selected_end_date output_foldername
```
The location of the generated GIF file within the output folder specified is returned when the script is finished running. _Note: The script will take more time for longer date ranges._

### Example

```shell
python main.py Novorossiysk 2021-12-01 2021-12-31 Novorossiysk_dec2021
```

**Valid base names**: Lesnovka, Klintsy, Unecha, Klimovo Air Base, Yelnya, Kursk, Pogonovo training ground,  Valuyki, Soloti, Opuk, Bakhchysarai, Novoozerne, Dzhankoi, Novorossiysk, Raevskaya 



