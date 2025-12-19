# Base Image: Use Miniconda3 to leverage Conda for environment management
FROM continuumio/miniconda3:latest

# --- Build Arguments and Environment Variables ---
# Define build-time argument for the application version
ARG APP_VERSION=0.0.0-local
# Set the application version as an environment variable
ENV APP_VERSION=${APP_VERSION}

# User ID mapping for shared network drives
ARG USER_ID=1000
ARG GROUP_ID=1000

# System dependencies
RUN apt-get update && apt-get install -y \
    git curl wget && \
    rm -rf /var/lib/apt/lists/*

# Create application user with matching host IDs
# Handle case where group ID already exists
RUN groupadd -g $GROUP_ID appuser 2>/dev/null || groupmod -n appuser $(getent group $GROUP_ID | cut -d: -f1) && \
    useradd -u $USER_ID -g $GROUP_ID -m appuser 2>/dev/null || usermod -l appuser -d /home/appuser -m $(getent passwd $USER_ID | cut -d: -f1)

# Set the application directory inside the container
WORKDIR /opt/app

# Copy the corrected Docker-compatible environment file first to leverage Docker's layer caching.
COPY environment-docker-fixed.yml .

# Create the Conda environment from the corrected environment file
RUN conda env create -f environment-docker-fixed.yml

# Copy the application source code and all supporting files
COPY app.py .
COPY src/ ./src/
COPY templates/ ./templates/
COPY utils/ ./utils/
COPY pages/ ./pages/

# Copy and set up the entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Volume mount points
RUN mkdir -p /data /workflow-scripts && \
    chown appuser:appuser /data /workflow-scripts

# Change ownership of application directory to appuser
RUN chown -R appuser:appuser /opt/app

# Switch to the application user
USER appuser

ENTRYPOINT ["/opt/app/entrypoint.sh"]

# Expose the port Streamlit runs on
EXPOSE 8501

# Set the default command to run the Streamlit app
# This will be executed by the entrypoint script
CMD ["streamlit", "run", "/opt/app/app.py"]