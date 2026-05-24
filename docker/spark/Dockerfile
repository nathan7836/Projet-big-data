FROM apache/spark:3.5.4
USER root
COPY jars/mysql-connector-j.jar /opt/spark/jars/mysql-connector-j.jar
COPY jars/postgresql.jar /opt/spark/jars/postgresql.jar
COPY jars/hadoop-aws-3.3.4.jar /opt/spark/jars/hadoop-aws-3.3.4.jar
COPY jars/aws-java-sdk-bundle-1.12.262.jar /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar
USER spark
