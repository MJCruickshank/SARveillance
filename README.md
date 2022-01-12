# SARveillance
Sentinel-1 SAR time series analysis for OSINT use. 

![image](https://user-images.githubusercontent.com/78884789/149216331-ea07a3cd-c4f5-4359-9b13-a87bd62ca801.png)
## Description 

Generates a time lapse GIF of the Sentinel-1 satellite images for the location and date range specified.

## Getting Started

### Requirements

- **Python 3.9** 
- **conda**: The installation script that installs the dependencies needs to use both conda and pip to fetch the required dependencies, so please use conda and create a new conda virtual environment.

### Installing Package Dependencies

1. Create the conda environment. This will install all necessary package dependencies too.

```shell
conda env create -f environment.yml
```

2. Activate the conda environment created.

```shell
conda activate SARveillance-conda-env
```

## To Run

### As a webapp hosted locally

```shell
streamlit run webapp.py
```

### As a command line tool
Run the `main.py` script. This will generate the time lapse GIF for the location and date range specified and save it to the output folder specified.

```shell
python main.py selected_base_name selected_start_date selected_end_date output_foldername
```
The location of the generated GIF file within the output folder specified is returned when the script is finished running. _Note: The script will take more time for longer date ranges._

**EXAMPLE**

```shell
python main.py Novorossiysk 2021-12-01 2021-12-31 Novorossiysk_dec2021
```

**Valid base names**: Lesnovka, Klintsy, Unecha, Klimovo Air Base, Yelnya, Kursk, Pogonovo training ground,  Valuyki, Soloti, Opuk, Bakhchysarai, Novoozerne, Dzhankoi, Novorossiysk, Raevskaya 



