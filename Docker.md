# SARveillance with Docker
Sentinel-1 SAR time series analysis for OSINT use. 

### Steps to make it work

1. create an image

```shell
docker build --no-cache --tag sarveillance .
```

2. start a container for earthengine authentication

```shell
docker-compose -f .\docker-compose.auth.yml run --rm sarveillance bash
```

This will show the auth url and lets you enter the authorization code. Thereafter a credentials file will be generated on your host engine in the "SARveillance/earthengine" folder.

3. now run the normal container

```shell
docker-compose up
```

You can now open your browser at localhost:8501. All generate images will be saved under "SARveillance/data". You can also edit your points of interests by changing the file "SARveillance/poi/poi_df.csv" and refresh the browser.