# Deterministic Docker Build - Uses exact package lock files
# Pin base image by SHA to prevent base image drift
FROM continuumio/miniconda3@sha256:4a2425c3ca891633e5a27280120f3fb6d5960a0f509b7594632cdd5bb8cbaea8

# --- Build Arguments and Environment Variables ---
ARG APP_VERSION=0.0.0-local
ARG COMMIT_SHA=unknown
ARG BUILD_DATE=unknown

ENV APP_VERSION=${APP_VERSION}
ENV COMMIT_SHA=${COMMIT_SHA}
ENV BUILD_DATE=${BUILD_DATE}

# User ID mapping for shared network drives
ARG USER_ID=1000
ARG GROUP_ID=1000

# System dependencies with pinned versions for reproducibility
RUN apt-get update && apt-get install -y \
    git=1:2.39.5-0+deb12u2 \
    curl=7.88.1-10+deb12u14 \
    wget=1.21.3-1+deb12u1 \
    && rm -rf /var/lib/apt/lists/*

# Create application user with matching host IDs
RUN groupadd -g $GROUP_ID appuser 2>/dev/null || groupmod -n appuser $(getent group $GROUP_ID | cut -d: -f1) && \
    useradd -u $USER_ID -g $GROUP_ID -m appuser 2>/dev/null || usermod -l appuser -d /home/appuser -m $(getent passwd $USER_ID | cut -d: -f1)

# Add version labels for update detection and repository linking
LABEL org.opencontainers.image.source="https://github.com/rrmalmstrom/sip_lims_workflow_manager" \
      org.opencontainers.image.url="https://github.com/rrmalmstrom/sip_lims_workflow_manager" \
      org.opencontainers.image.documentation="https://github.com/rrmalmstrom/sip_lims_workflow_manager" \
      org.opencontainers.image.title="SIP LIMS Workflow Manager" \
      org.opencontainers.image.description="LIMS Workflow Manager with Python scripts for processing SIP metagenomic files" \
      org.opencontainers.image.revision="${COMMIT_SHA}" \
      com.sip-lims.commit-sha="${COMMIT_SHA}" \
      com.sip-lims.build-date="${BUILD_DATE}" \
      com.sip-lims.version="${APP_VERSION}" \
      com.sip-lims.build-type="deterministic"

# Set the application directory inside the container
WORKDIR /opt/app

# Copy conda lock file and create environment with exact packages
COPY conda-lock.txt .
RUN conda create --name sip-lims-workflow-manager --file conda-lock.txt

# Copy pip lock file and install exact pip packages
COPY requirements-lock.txt .
RUN /opt/conda/envs/sip-lims-workflow-manager/bin/python -m pip install -r requirements-lock.txt --no-deps

# Copy the application source code and all supporting files
COPY app.py .
COPY src/ ./src/
COPY templates/ ./templates/
COPY utils/ ./utils/

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
CMD ["streamlit", "run", "/opt/app/app.py"]