FROM nvidia/cuda:11.2.2-runtime-ubuntu20.04

# Install some basic utilities
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    sudo \
    git \
    bzip2 \
    libx11-6 \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
# Create a non-root user and switch to it
# RUN adduser --disabled-password --gecos '' --shell /bin/bash user \
#  && chown -R user:user /app
# RUN echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-user
# USER user

# All users can use /home/user as their home directory
# ENV HOME=/home/user
# RUN chmod 777 /home/user

ENV CONDA_AUTO_UPDATE_CONDA=false
ENV PATH /opt/conda/bin:$PATH
RUN curl -sLo ~/miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-4.7.12.1-Linux-x86_64.sh \
 && chmod +x ~/miniconda.sh \
 && /bin/bash ~/miniconda.sh -b -p /opt/conda \
 && rm ~/miniconda.sh \
 && conda install -y python==3.9.5 \
 && conda clean -ya

RUN conda install pytorch==1.11 cudatoolkit=10.2 -c pytorch -y
RUN pip install tensorflow==2.8.0
RUN pip install protobuf==3.20.*
RUN pip install pillow==9.2.0
RUN pip install pygame==2.0.1
RUN pip install pyyaml==6.0
RUN pip install stable_baselines3==1.1.0a7
RUN pip install ray[rllib]==1.10.0
RUN pip install setuptools==65.5.0 pip==21
RUN pip install wheel==0.38.0
#RUN pip install -U https://s3-us-west-2.amazonaws.com/ray-wheels/latest/ray-3.0.0.dev0-cp38-cp38-manylinux2014_x86_64.whl

# Copy the requirements text into the container at /
ADD /requirements.txt /

# install dependencies
RUN pip install -r requirements.txt

# Create a directory to mount homework at run 
RUN mkdir src2

# Set the working directory to /src
WORKDIR /src2

EXPOSE 8889

# Install the package and run ipython in no-browser mode
CMD ["sh", "-c", "pip install -e . && jupyter notebook --ip=0.0.0.0 --no-browser --allow-root --port=8889"]

