FROM continuumio/miniconda3:4.10.3-alpine

# create directory needed for ee authentication
RUN mkdir -p /root/.config/earthengine/

# create the environment
COPY environment.yml .
RUN conda env create -f environment.yml

# copy entrypoint.sh
COPY entrypoint.sh .
RUN chmod +x ./entrypoint.sh

# copy entrypoint.auth.sh
COPY entrypoint.auth.sh .
RUN chmod +x ./entrypoint.auth.sh

# set workdir
WORKDIR /opt/sarveillance

# make run commands to use the new env
RUN echo "conda activate SARveillance-conda-env" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

# entrypoint
# ENTRYPOINT ["/entrypoint.sh"]
