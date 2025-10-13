# Base Image: Use Miniconda3 to leverage Conda for environment management
FROM continuumio/miniconda3:latest

# --- Build Arguments and Environment Variables ---
# Define build-time argument for the application version
ARG APP_VERSION=0.0.0-local
# Set the application version as an environment variable
ENV APP_VERSION=${APP_VERSION}

# Set the application directory inside the container
WORKDIR /opt/app

# Copy the environment file first to leverage Docker's layer caching.
COPY environment.yml .

# Create the Conda environment from the environment.yml file
RUN conda env create -f environment.yml

# Copy the application source code and all supporting files
COPY app.py .
COPY src/ ./src/
COPY templates/ ./templates/
COPY utils/ ./utils/

# Copy and set up the entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/opt/app/entrypoint.sh"]

# Expose the port Streamlit runs on
EXPOSE 8501

# Set the default command to run the Streamlit app
# This will be executed by the entrypoint script
CMD ["streamlit", "run", "/opt/app/app.py"]