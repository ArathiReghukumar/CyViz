# CyViz

#Proposal:
Implement an application that would provide a time based visualization of  the citation of research publications.
Each paper has time when it was created. This lets us view the citation network as a dynamic graph.
Visualize change in paper influence and establish paradigm shifts in a field (when a new paper establishes a completely new and better way of doing things)
Visualize change in research interests of specific authors
Explore interplay between topics in a field over time

#Dataset - OpenAlex

Huge open source collection of indexed research paper abstracts and metadata
~ 250GB zipped json data
~ 7KB per record

5 types of entities present in the database
Works - Research papers, books etc.
Authors
Venues - Journals, Conferences
Institutions - Organizations affiliated with the authors
Concepts - Topic specific tags

#Target Users:
Authors of publications.
Researchers interested in the domain.
Fellow research enthusiasts.

#Methodology/ Tools used:
Dataset subset obtained from OpenAlex using API and stored in a NoSQL database
Total dataset is at rest
Sections will be streamed and processed

Backend: Python, Flask, NetworkX
Frontend: HTML/CSS/JS, AntV - G6, Amcharts 
Datastore: MongoDB


