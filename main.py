from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field , computed_field #Optional
from fastapi.responses import JSONResponse
from typing import Annotated, Literal, Optional
import json

app = FastAPI()

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the patient", example="P001")]
    name: Annotated[str, Field(..., description="Name of the patient")]
    city: Annotated[str, Field(..., description="City of the patient")]
    age: Annotated[int, Field(..., description="Age of the patient, must be a positive integer", ge=0, lt=120)]
    gender: Annotated[Literal["male", "female", "Other"], Field(..., description="Gender of the patient")]
    height: Annotated[float, Field(..., descripiton="Height of the patient in meters", ge=0)]
    weight: Annotated[float, Field(..., description="Weight of the patient in kg", ge=0)]

    @computed_field
    @property
    def bmi(self) -> float:
        
        bmi = round(self.weight / (self.height ** 2), 2) 
        return bmi
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 30:
            return "Normal"
        elif self.bmi >30:
            return "Overweight"
        else:
            return "Obese"   
        
class PatientUpdate(BaseModel):
    
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female', 'Other']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]        
    weight: Annotated[Optional[float], Field(default=None, gt=0)]  
    
# Function for loading data from json file
def load_data():
    with open ('patient.json', 'r') as f:
        data=json.load(f)
    return data    

def save_data(data):
    with open ('patient.json', 'w') as f:
        json.dump(data, f)
        
@app.get("/")
def hello():
    return {'message':'Patient Management System API'}

@app.get("/about")
def About():
    return{'message':'This is an API for patient management system'}

# Endpoint for getting patient data(view)
@app.get("/view")
def View():
     data = load_data()
     
     return data
 

@app.get("/patient/{patient_id}")
def view_patient(
    patient_id: str = Path(..., description="Enter patient ID", examples={"example1": {"value": "P001"}})
):
    data = load_data()  # Make sure load_data() returns a dictionary
    
    if patient_id in data:
        return data[patient_id]
    
    # Correct way to return an error
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/sort")
def sort_patients(sort_by : str = Query(..., description='Sort on the basis of height, weight or bmi'), order: str = Query('asc', description = 'Sort in asc or decs order')):
    
    valid_fields = ['height', 'weight', 'bmi']
    
    if sort_by not in valid_fields:
        raise HTTPException(status_code=404, detail=f'Invalid field select from {valid_fields}')
    
    if order not in ['asc', 'decs']:
        raise HTTPException(status_code=404, detail='Invalid order select between asc or desc')
    
    data = load_data()
    
    sort_order= True if order =='decs' else False 
    
    sorted_data = sorted(data.values(), key= lambda x : x.get(sort_by, 0), reverse=sort_order)
    
    return sorted_data

@app.post("/create")
def create_patient(patient: Patient):
    
    data = load_data()
    
    # check if patient already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")
    
    # adding new patient to the database 
    data[patient.id] = patient.model_dump(exclude=['id'])
    
    # saving the data
    save_data(data)
    
    return JSONResponse(status_code=201, content={'message':'Patient created successfully'})

@app.put("/edit/{patient_id}")
def edit_patient(patient_id: str, patient_update: PatientUpdate):
    
    data = load_data()
    
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    existing_patient_info = data[patient_id]
    
    updated_patient_info = patient_update.model_dump(exclude_unset=True) # exclude unset for not including the default none values
    
    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value
    
    #creating pydantic object for calculating computed fields
    existing_patient_info['id'] = patient_id 
    patient_pydantic_object = Patient(**existing_patient_info)
    
    existing_patient_info = patient_pydantic_object.model_dump(exclude={'id'})
    
    #adding dict to data
    data[patient_id] = existing_patient_info    
    
    save_data(data)
    
    return JSONResponse(status_code=200, content = {'message' : 'Patient updated successfully'})


@app.delete('/delete/{patient_id}')
def delete(patient_id: str):
  
   data= load_data()
   
   if patient_id not in data:
       raise HTTPException(status_code=404, detail='Patient not found')
   
   del data[patient_id]
   
   save_data(data)
   
   return JSONResponse(status_code=200, content={'message' : 'Patient deleted Successfully'})
