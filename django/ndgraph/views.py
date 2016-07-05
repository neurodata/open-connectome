# Copyright 2014 NeuroData (http://neurodata.io)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.core.files.base import ContentFile
from wsgiref.util import FileWrapper

import os
import re
from contextlib import closing
import tarfile

from ndwserror import NDWSError
import ndgraph
import logging
logger=logging.getLogger("neurodata")

@login_required(login_url='/nd/accounts/login/')`
def buildGraph (request, webargs):
    """Build a graph based on different arguments"""
    try:
        (file, filename) = ndgraph.genGraphRAMON (*((webargs.replace(',','/').split('/'))[0:-1]))
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = "attachment; filename=\"output.{}\"".format(filename)
        response.write(file.read())
        return response
    except Exception as e:
        logger.warning(e)
        raise NDWSError(e)