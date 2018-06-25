# python:alpine is 3.{latest}
FROM python:alpine 

# prevent numpy from failing with no gcc,
# as per https://wired-world.com/?p=100
RUN apk add --update curl gcc g++ \
    && rm -rf /var/cache/apk/*

RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME World

# Run when the container launches
ENTRYPOINT ["python", "/app/run.py"]
# CMD /bin/sh
# ENTRYPOINT ["/bin/sh"]
# ENTRYPOINT /bin/sh
