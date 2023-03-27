# Build a CentOS based system
FROM brunneis/python:3.7.0-ubuntu-18.04


RUN apt-get -y update && apt-get install -y \
  wget \
  unzip \
  build-essential \
  xutils-dev \
  default-jre \
  python3-pip \
  cmake

RUN pip3 install -U pip

RUN pip3 install wget
RUN pip3 install requests
RUN pip3 install pydicom
RUN pip3 install SimpleITK
RUN pip3 install tqdm
RUN pip3 install argparse
RUN pip3 install pyyaml
RUN pip3 install multiprocess
RUN pip3 install numpy
RUN pip3 install pyplastimatch
WORKDIR /

# DCMTK (Offis DICOM Toolkit)
# http://dcmtk.org/dcmtk.php.en
RUN apt-get install -y dcmtk
RUN apt-get install -y plastimatch
RUN apt-get install -y git



# change to top level directory
WORKDIR /


# cleanup
RUN apt-get purge -y build-essential xutils-dev
RUN apt-get clean autoclean
RUN apt-get autoremove -y
RUN rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*