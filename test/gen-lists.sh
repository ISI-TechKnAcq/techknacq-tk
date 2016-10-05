#!/bin/bash

# Generate reading lists for our standard queries.

echo "# Machine Translation"
echo

../reading-list $1 machine translation

echo
echo

echo "# Dependency Parsing"
echo

../reading-list $1 dependency parsing

echo
echo

echo "# Sentiment Analysis"
echo

../reading-list $1 sentiment analysis

echo
echo

echo "# Speech Recognition"
echo

../reading-list $1 speech recognition

echo
echo

echo "# Document Summarization"
echo

../reading-list $1 document summarization

echo
echo

echo "# Machine Learning"
echo

../reading-list $1 machine learning

echo
