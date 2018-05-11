## Pure FA Swagger Generator

This is a tool that converts the Pure FlashArray API pdf documentation into an interactive Swagger UI.  This lets your browse the API documentation in a convient format and even execute API calls interactively directly to a FlashArray!


# Try It: 
Requires [docker](https://docs.docker.com/install/) to be installed
docker run -it --rm -p 80:5000 sile16/pureswagger 

Then open your browser to http://127.0.0.1 (use firefox to enable real time API calls!)
Then load a [FlashArray REST pdf from Pure Support](https://support.purestorage.com/FlashArray/PurityFA/Purity_FA_REST_API/Reference/REST_API_PDF_Reference_Guides)

That's it!

#To stop run:
just ctrl^c on the console docker container 
