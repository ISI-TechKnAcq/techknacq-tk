FROM debian:latest

MAINTAINER Jonathan Gordon <jgordon@isi.edu>

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# Install system dependencies.

ARG DEBIAN_FRONTEND=noninteractive

RUN echo deb http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main \
    | tee /etc/apt/sources.list.d/webupd8team-java.list
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys EEA14886

RUN apt-get update -q -y --fix-missing
RUN apt-get upgrade -q -y --fix-missing

RUN apt-get install -q -y --fix-missing wget bzip2 git g++ make enchant \
        poppler-utils

RUN echo debconf shared/accepted-oracle-license-v1-1 select true | \
    debconf-set-selections && \
    apt-get install -q -y --fix-missing oracle-java8-installer \
        oracle-java8-set-default maven

RUN apt-get clean -q

RUN rm -rf /var/cache/oracle-jdk8-installer


# Install Miniconda.

RUN wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
         -O ~/miniconda.sh --quiet && \
    bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh

ENV PATH /opt/conda/bin:$PATH

RUN conda update -y conda

RUN conda install numpy nltk beautifulsoup4 lxml networkx flask flask-cors \
                  click
RUN pip install pyenchant ftfy noaho wikipedia


# Install NLTK data.

RUN mkdir -p /usr/share/nltk_data && \
    python -m nltk.downloader -d /usr/share/nltk_data punkt wordnet


# Install external tools.

RUN mkdir -p /t/ext

WORKDIR /t/ext


# Install Mallet.

RUN wget http://mallet.cs.umass.edu/dist/mallet-2.0.8RC3.tar.gz --quiet && \
    tar xvf mallet-2.0.8RC3.tar.gz && \
    mv mallet-2.0.8RC3 mallet && \
    rm mallet-2.0.8RC3.tar.gz


# Install Infomap.

RUN wget http://www.mapequation.org/downloads/Infomap.zip --quiet && \
    unzip Infomap.zip -d infomap && \
    rm Infomap.zip && \
    cd infomap && \
    make


# Install Elasticsearch.

ENV ES_PKG_NAME elasticsearch-1.5.0

RUN wget https://download.elasticsearch.org/elasticsearch/elasticsearch/$ES_PKG_NAME.tar.gz --quiet && \
    tar xvzf $ES_PKG_NAME.tar.gz && \
    rm -f $ES_PKG_NAME.tar.gz && \
    mv $ES_PKG_NAME elasticsearch


# Check out and compile TechKnAcq Core.

RUN git clone https://github.com/ISI-TechKnAcq/techknacq-core.git && \
    cd techknacq-core && \
    mvn package


# Check out and compile TechKnAcq Server.

# Copy ssh keys so you can check out the private repository.
ADD repo-key /t/repo-key
RUN chmod 0400 /t/repo-key
RUN echo "IdentityFile /t/repo-key" >> /etc/ssh/ssh_config && \
    echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config

RUN git clone -b techknacq-tk-integration \
        git@github.com:ISI-TechKnAcq/techknacq-server.git && \
    cd techknacq-server && \
    mvn package

RUN ln -s /t/data/server/application.properties \
          /t/ext/techknacq-server/application-production.properties

# Add TechKnAcq Toolkit.

ADD lib /t/lib
ADD build-corpus /t
ADD concept-graph /t
ADD reading-list /t
ADD server /t
ADD start-server /t

ENV PYTHONPATH /t/lib:$PYTHONPATH


# Run TechKnAcq.

ENV MAVEN_OPTS "-Xms1024m -Xmx4096m"

WORKDIR /t


# Elasticsearch HTTP
EXPOSE 9200
# Elasticsearch transport
EXPOSE 9300
# TechKnAcq-tk Server
EXPOSE 9797
# TechKnAcq Server
EXPOSE 9999
