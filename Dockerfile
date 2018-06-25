# based on python:3
FROM jjuanda/numpy-pandas

# Set the working directory to /app
WORKDIR /

# Install any needed packages specified in requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container at /app
ADD . /

# Make port 80 available to the world outside this container
EXPOSE 5000

ENTRYPOINT ["python", "/run.py"]
