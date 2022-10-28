# VERSION: 0.1.0
# DESCRIPTION: Basic extensible Jupyter Notebook/Lab Container
# BUILD: docker build --rm -t docker-jupyter-extensible .
FROM jupyter/scipy-notebook:latest

USER root

USER $NB_UID

# install Python packages you often use
RUN pip install --upgrade pip
RUN pip install psycopg2-binary~=2.9.4 \
    tensorflow
    # choose the python packages you need
    #&& fix-permissions "${CONDA_DIR}" \
    #&& fix-permissions "/home/${NB_USER}"