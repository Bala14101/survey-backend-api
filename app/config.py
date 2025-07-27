import os
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

# MONGO_URI = MongoClient(os.getenv("MONGO_URI"))
MONGO_URI = MongoClient(os.getenv("MONGO_URI_PRODUCTION"))

DATABASE = MONGO_URI[os.getenv("DATABASE")]

print("mongourl", MONGO_URI)
PersonMaster = DATABASE[os.getenv("PersonMaster")]
SurveyQuestionMaster = DATABASE[os.getenv("SurveyQuestionMaster")]
QuestionMaster = DATABASE[os.getenv("QuestionMaster")]
PersonLinkDetails = DATABASE[os.getenv("PersonLinkDetails")]
PersonSurveyDetails = DATABASE[os.getenv("PersonSurveyDetails")]
CompanySurveyMaster = DATABASE[os.getenv("CompanySurveyMaster")]
SurveySkipLogicConfig = DATABASE[os.getenv("SurveySkipLogicConfig")]
SurveyOptionRestrictionConfig = DATABASE[os.getenv("SurveyOptionRestrictionConfig")]
SurveyPrefaceConfig=DATABASE[os.getenv("SurveyPrefaceConfig")]
# PersonMaster = DATABASE[os.getenv("PersonMaster")]

# (Optional) test print
print("Connected to DB:", DATABASE.name)
print("Using collection:", PersonMaster.name)
print("Using collection:", PersonLinkDetails.name)

