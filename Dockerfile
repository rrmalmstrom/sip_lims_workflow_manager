# Base Image: Use Miniconda3 to leverage Conda for environment management
FROM continuumio/miniconda3:latest

# Set the working directory inside the container
WORKDIR /app

# Copy the environment file first to leverage Docker's layer caching.
# This step will only be re-run if the environment.yml file changes.
COPY environment.yml .

# Create the Conda environment from the environment.yml file
# This installs all necessary dependencies into an environment named 'sip-lims'
RUN conda env create -f environment.yml

# Copy the rest of the application source code into the working directory
COPY . .

# No entrypoint or command is specified by default.
# The command will be provided by the run/test scripts.