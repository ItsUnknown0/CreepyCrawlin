import asyncio
import json
import warnings

async def ContainsKeywords(InputKeywords : list, found_description : str, found_keywords : str, found_title : str, paragraphsList : list):
    for word in InputKeywords:
        word : str = word.lower()

        if found_description != None and word in found_description.lower():
            return True
        
        if found_keywords != None and word in found_keywords.lower():
            return True
        
        if found_title != None and word in found_title.lower():
            return True
            
        # go through each paragraph
        for paragraph in paragraphsList:
            textContent = await paragraph.getProperty("textContent")
            convertedText = await textContent.jsonValue()
            if word in convertedText:
                return True
    
    return False

async def CheckMetaData(HeadElement, BodyElement):
    siteDescription = None
    siteKeywords = None
    siteStructuredData = None

    try:
        if HeadElement:
            # Getting Meta Data

            MetadataList = await HeadElement.querySelectorAll("meta")
            
            for meta in MetadataList:
                name = await meta.getProperty("name")

                if name and await name.jsonValue() == "description":
                    metaTextContent = await meta.getProperty("content")
                    siteDescription = await metaTextContent.jsonValue()
                elif name and await name.jsonValue() == "keywords":
                    metaTextContent = await meta.getProperty("content")
                    siteKeywords = await metaTextContent.jsonValue()

            # Getting all paragraphs
            ParagraphsList = await HeadElement.querySelectorAll("p")
            
            # Getting Structured Data

            ScriptsList = await HeadElement.querySelectorAll("script")

            for script in ScriptsList:
                scriptType = await script.getProperty("type")

                if scriptType and await scriptType.jsonValue() == "application/ld+json":
                    textContent = await script.getProperty("textContent")
                    convertedContent = await textContent.jsonValue()
                    siteStructuredData = json.loads(convertedContent)
    except Exception as msg:
        warnings.warn(f"Something went wrong with CheckMetaData(): {msg}")
        return None, None, None

    return siteDescription, siteKeywords, ParagraphsList, siteStructuredData

async def ScrapeMain(InputKeywords : list, HeadElement, BodyElement, SiteTitle : str):
    siteDescription, siteKeywords, paragraphsList, siteStructuredData = await CheckMetaData(HeadElement,BodyElement)

    HasKeywords = await ContainsKeywords(InputKeywords,siteDescription, siteKeywords, SiteTitle, paragraphsList)

    if HasKeywords:
        return siteDescription, siteKeywords, siteStructuredData
    else:
        return None, None, None
