from flask import jsonify,request
from bson import ObjectId,json_util

from datetime import datetime

from app.config import PersonMaster,SurveyQuestionMaster,QuestionMaster,PersonLinkDetails,CompanySurveyMaster,PersonSurveyDetails,SurveySkipLogicConfig,SurveyOptionRestrictionConfig,SurveyPrefaceConfig

def register_routes(app):

    @app.route('/test')
    def test():
        return jsonify({"ok": True})

    @app.route("/",methods=["GET"])
    def hello():
        return jsonify({"message":"Hello from backend"})
    
    @app.route("/get_user/<person_id>")
    def fetch_user(person_id):
            print("enter route")
            all_users = list(PersonMaster.find({}, {"_id": 0}))

            print("all users", all_users)
            user = PersonMaster.find_one({"PersonId": person_id}, {"_id": 0})
            print("user", user)
            if user:
                return jsonify({'user': user}), 200
            else:
                return jsonify({'error': 'User not found'}), 404
            
    @app.route("/fetchSurveyQuestions/<surveyId>")  
    def fetch_questions(surveyId: str):
            # Fetch the survey details from SurveyQuestionMaster
            survey = SurveyQuestionMaster.find_one({"SurveyId": surveyId})
            if not survey:
                raise Exception(status_code=404, detail="Survey not found")

            # Extract all question IDs from the survey and map them to survey question numbers
            question_id_to_surveyQuestionNo_mandatory_mapping = {}
            survey_questions_data = survey.get("Questions", {})

            for section_name, questions in survey_questions_data.items():
                for question in questions:
                    question_id = question["QuestionId"]
                    survey_question_no = question["SurveyQuestionNo"]
                    mandatory_condition = question["Mandatory"]
                    footer_text = question["FooterText"]

                    
                    # If the QuestionId is already in the mapping, skip adding it again
                    if question_id not in question_id_to_surveyQuestionNo_mandatory_mapping:
                        question_id_to_surveyQuestionNo_mandatory_mapping[question_id]={
                              "SurveyQuestionNo": survey_question_no,
                                "Mandatory": mandatory_condition,
                                "FooterText":footer_text
                        }


            # Fetch all unique question IDs from the survey_questions_data
            survey_question_ids = list(question_id_to_surveyQuestionNo_mandatory_mapping.keys())

            # Fetch the questions from QuestionMaster
            questions_cursor = QuestionMaster.find({"QuestionId": {"$in": survey_question_ids}})
            survey_questions = list(questions_cursor)

            # Adjust SurveyQuestionNo for each question based on the mapping
            for question in survey_questions:
                if '_id' in question:
                    question['_id'] = str(question['_id'])

                addition_details_for_question_to_map =  question_id_to_surveyQuestionNo_mandatory_mapping.get(question["QuestionId"])
                if addition_details_for_question_to_map:
                    question["SurveyQuestionNo"] = addition_details_for_question_to_map.get("SurveyQuestionNo")
                    question["Mandatory"] = addition_details_for_question_to_map.get("Mandatory")
                    question["FooterText"] = addition_details_for_question_to_map.get("FooterText") or ""
            # Organize questions section-wise
            survey_questions_sectionwise = {}

            for section_name, section_questions in survey_questions_data.items():
                section_questions_data = []
                for question in section_questions:
                    question_id = question["QuestionId"]
                    question_data = next((q for q in survey_questions if q["QuestionId"] == question_id), None)
                    if question_data:
                        section_questions_data.append(question_data)
                survey_questions_sectionwise[section_name] = section_questions_data

            return survey_questions_sectionwise
        
    @app.route("/fetchPersonLinkDetails/<pcs_link_id>")
    def fetch_person_link_details(pcs_link_id):
        print("pcslinkid", pcs_link_id)
        personLinkDetails = PersonLinkDetails.find_one({"PCSLinkId": pcs_link_id})
        print("personLinkDetails", personLinkDetails)
        if personLinkDetails:
            personLinkDetails['_id'] = str(personLinkDetails['_id'])
            return jsonify({'personLinkDetails':personLinkDetails})
        else:
            return jsonify({'error': 'User not found'}), 404

    @app.route("/fetchSurveySections/<surveyId>")
    def fetch_survey_sections(surveyId:str):
            survey = SurveyQuestionMaster.find_one({"SurveyId": surveyId})
            if not survey:
                raise Exception(status_code=404, detail="Survey not found")

            survey_questions_data = survey.get("Questions", {})
            survey_sections = []

            for section_name, questions in survey_questions_data.items():
                for question in questions:
                    survey_sections.append(question["SectionName"])
                    break
            return survey_sections

    @app.route("/fetchPersonSurveys/<person_id>")
    def fetch_person_surveys(person_id):
        person_link_details = PersonLinkDetails.find({"PersonId": person_id})
        surveys = []
        # company_survey_status = None

        # Counters for each survey status
        in_progress_count = 0
        submitted_count = 0
        not_started_count = 0
    
        for link_detail in person_link_details:
            company_survey_id = link_detail.get("CompanySurveyId")
            company_id = company_survey_id.split("-")[0]
            survey_id = company_survey_id.split("-")[1]
            
            company_survey_details = CompanySurveyMaster.find_one({"CompanyId": company_id},{"_id":0,"CompanySurveys":1})
            if company_survey_details:
                for key in company_survey_details:
                    if isinstance(company_survey_details[key], ObjectId):
                        company_survey_details[key] = str(company_survey_details[key])
            
            company_surveys = company_survey_details["CompanySurveys"]
            for survey in company_surveys:
                if survey["CompanySurveyId"] == company_survey_id:
                    company_survey_status = survey["SurveyStatus"]
                    
            survey_data = SurveyQuestionMaster.find_one({"SurveyId": survey_id})
            if survey_data:
                survey_name = survey_data.get("SurveyName")
                person_survey_details = PersonSurveyDetails.find_one({"PersonId": person_id, "CompanySurveyId": company_survey_id})
                if person_survey_details:
                    status = person_survey_details.get("PersonSurveyStatus")
                    if status == "in-progress":
                        in_progress_count += 1
                        status="In Progress"
                    elif status == "submitted":
                        submitted_count += 1
                        status="Submitted"
                    actual_date_raw = link_detail.get("LinkSentDateTime")
                else:
                    not_started_count += 1
                    status = "Not Started"
                    actual_date_raw = link_detail.get("LinkSentDateTime", "N/A")
    
                # Format the date to only show the date part
                if isinstance(actual_date_raw, datetime):
                    actual_date = actual_date_raw.strftime('%Y-%m-%d')
                else:
                    actual_date = "N/A"

                surveys.append({
                    "survey_id":survey_id,
                    "survey_name": survey_name,
                    "company_survey_id": company_survey_id,
                    "status": status,
                    "actual_date": actual_date,
                    "company_survey_status":company_survey_status
                })

        return jsonify({
            "surveys_not_started":not_started_count,
            "surveys_in_progess":in_progress_count,
            "surveys_completed":submitted_count,
            "surveys_list":surveys})        
    
    @app.route("/fetchSurveySkipLogicConfig/<surveyId>")
    def fetch_skip_logic(surveyId: str):
        survey =  SurveySkipLogicConfig.find_one({"SurveyId": surveyId},{"_id": 0})

        if survey:
            return jsonify((survey)), 200
        else:
            return jsonify({"error": "Survey not found"}), 404
    
    @app.route("/fetchSurveyOptionRestrictionConfig/<surveyId>")
    def fetch_survey_option_restriction(surveyId:str):
        survey = SurveyOptionRestrictionConfig.find_one({"SurveyId": surveyId},{"_id": 0})
        if survey:
            return jsonify((survey)), 200
        else:
            return jsonify({"error": "Survey not found"}), 404
        
    @app.route("/fetchSurveyPrefaceConfig/<surveyId>")
    def fetch_survey_preface(surveyId:str):
            survey = SurveyPrefaceConfig.find_one({"SurveyId": surveyId},{"_id": 0})
            if survey:
                return jsonify((survey)), 200
            else:
                return jsonify({"error": "Survey not found"}), 404
            
    @app.route("/get_survey_responses/<pcs_link_id>")
    def get_survey_responses(pcs_link_id):
        try:
            response = PersonSurveyDetails.find_one({"PCSLinkId": pcs_link_id})
            if not response:
                return jsonify({"message": "No survey responses found"}), 404
                # Convert the response to a JSON-serializable format
            response_serializable = json_util.dumps(response)
            return response_serializable
        except Exception as e:
            return jsonify({"message": "Error fetching responses", "error": str(e)}), 500   
        
    # @self.login_required
    # for saving all questions response
    @app.route("/save_survey_responses",methods=["POST"])
    def save_survey_responses():
        # try:
            data = request.json
            CompanySurveyId = data['CompanySurveyId']
            PersonSurveyStartDateTime = data["PersonSurveyStartDateTime"]
            PersonSurveyStatus = data["PersonSurveyStatus"]
            responses = data['Questions']
            PersonId = data['PersonId']
            PCSLink_id=data['PCSLinkId']
            QuestionsSequence = data['QuestionsSequence']
            NeverAskQuestionsSequence = data['NeverAskQuestionsSequence']
            SurveySectionsFlow = data['SurveySectionsFlow']
            existing_response = PersonSurveyDetails.find_one({"PCSLinkId": PCSLink_id})
            
            # if existing_response:
            #     PersonSurveyDetails.update_one(
            #         {"PCSLinkId": PCSLink_id},
            #         {"$unset": {"Questions": "","PersonSurveyStatus":""}}
            #     )
            #     result = PersonSurveyDetails.update_one(
            #         {"PCSLinkId": PCSLink_id},
            #         {"$set": {"Questions": responses,
            #                     "PersonSurveyStatus":PersonSurveyStatus,
            #                     "QuestionsSequence" : QuestionsSequence,
            #                     "NeverAskQuestionsSequence" : NeverAskQuestionsSequence,
            #                     "SurveySectionsFlow" : SurveySectionsFlow
            #         }}

            #     )
            # else:
            # Insert new responses
            new_response = {
                "PCSLinkId":PCSLink_id,
                "CompanySurveyId": CompanySurveyId,
                "PersonSurveyStartDateTime":PersonSurveyStartDateTime,
                "PersonSurveyStatus":PersonSurveyStatus,
                "Questions": responses,
                "PersonId":PersonId,
                "QuestionsSequence" : QuestionsSequence,
                "NeverAskQuestionsSequence" : NeverAskQuestionsSequence,
                "SurveySectionsFlow" : SurveySectionsFlow
            }
            PersonSurveyDetails.insert_one(new_response)
        
            return jsonify({"message": "Responses saved successfully"}), 200

        # except Exception as e:
        #     return jsonify({"message": "Error saving responses", "error": str(e)}), 500