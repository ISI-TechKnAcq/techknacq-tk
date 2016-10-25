FROM debian:latest

MAINTAINER Jonathan Gordon <jgordon@isi.edu>

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8


# Install system dependencies.

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q -y --fix-missing
RUN apt-get upgrade -q -y --fix-missing

RUN apt-get install -q -y --fix-missing wget bzip2

RUN apt-get clean -q


# Install Miniconda.

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
         -O ~/miniconda.sh --quiet && \
    bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh

ENV PATH /opt/conda/bin:$PATH

RUN conda update -y conda


## Add TechKnAcq code.

ADD lib /t/lib
ADD build-corpus /t
ADD concept-graph /t
ADD reading-list /t
ADD server /t
