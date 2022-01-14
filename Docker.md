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

This will show the auth url and lets you enter the authorization code. This will generate a credentials file on your host in the "earthengine" folder in the sarveillance folder.

3. now run the normal container

```shell
docker-compose up
```

You can now open your browser at localhost:8501. All generate images will be saved in the sarveillance folder under "data". You cn also edit your points of interests by changing the file /poi/poi_df.csv and restart the container.