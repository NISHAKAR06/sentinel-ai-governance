FROM continuumio/miniconda3:4.10.3

# Working directory
WORKDIR /app

# Copy project files
COPY . /app

# Create and activate conda environment and install dependencies
RUN conda create -y -n sentinel python=3.11 && \
    /bin/bash -lc "source /opt/conda/bin/activate sentinel && pip install --no-cache-dir -r requirements.txt"

# Expose port used by the app
EXPOSE 8000

# Start the app using uvicorn inside the conda env
CMD ["/bin/bash", "-lc", "source /opt/conda/bin/activate sentinel && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
