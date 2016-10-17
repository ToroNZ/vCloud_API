#!/bin/bash

if [ "$EUID" -ne 0 ]
	then echo "Please run as root"
	exit
fi

YUM_PACKAGE_NAME = "python python-pip"
DEB_PACKAGE_NAME = "python python-pip"


if [[ ! -z $YUM_CMD ]]; then
	yum install -y $YUM_PACKAGE_NAME
  pip install inquirer
elif [[ ! -z $APT_GET_CMD ]]; then
	apt-get install -y $DEB_PACKAGE_NAME
  pip install inquirer
elif [[ ! -z $OTHER_CMD ]]; then
	$OTHER_CMD <proper arguments>
else
	echo "error can't install packages"
	exit 1;
fi
