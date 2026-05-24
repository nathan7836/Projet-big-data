#!/bin/bash
# Download JDBC drivers needed by Spark for the pipeline
set -e

JARS_DIR="$(cd "$(dirname "$0")/jars" && pwd)"
mkdir -p "$JARS_DIR"

echo "Downloading JDBC jars to $JARS_DIR ..."

# MySQL Connector/J 8.3.0
if [ ! -f "$JARS_DIR/mysql-connector-j.jar" ]; then
  echo "  -> MySQL Connector/J 8.3.0"
  curl -sL "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.3.0/mysql-connector-j-8.3.0.jar" \
    -o "$JARS_DIR/mysql-connector-j.jar"
fi

# PostgreSQL JDBC 42.7.1
if [ ! -f "$JARS_DIR/postgresql.jar" ]; then
  echo "  -> PostgreSQL JDBC 42.7.1"
  curl -sL "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.1/postgresql-42.7.1.jar" \
    -o "$JARS_DIR/postgresql.jar"
fi

# Hadoop AWS 3.3.4
if [ ! -f "$JARS_DIR/hadoop-aws-3.3.4.jar" ]; then
  echo "  -> Hadoop AWS 3.3.4"
  curl -sL "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar" \
    -o "$JARS_DIR/hadoop-aws-3.3.4.jar"
fi

# AWS Java SDK Bundle 1.12.262
if [ ! -f "$JARS_DIR/aws-java-sdk-bundle-1.12.262.jar" ]; then
  echo "  -> AWS Java SDK Bundle 1.12.262"
  curl -sL "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar" \
    -o "$JARS_DIR/aws-java-sdk-bundle-1.12.262.jar"
fi

echo "All JARs downloaded:"
ls -lh "$JARS_DIR"/*.jar
