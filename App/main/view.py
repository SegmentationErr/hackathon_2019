from flask import render_template, Blueprint,redirect,request,flash
from werkzeug import secure_filename
import os
from App.api.foodAPI import Food
from App.implement import *
from backend.google_vision import getJson
from backend.analyze import toDataFrame
from backend.classification import *
import sys
import numpy as np

f = Food()
data = f.generate_recipe_card()
# print(data)
model = Classifier()

main_blueprint = Blueprint(
    'main',
    __name__,
    static_folder = 'static',
    template_folder = 'templates'
)

UPLOAD_FOLDER = './App/main/static/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

@main_blueprint.route('/detail_recipe', methods=['POST','GET'])
def detail_recipe():
	if request.method == 'POST':
		recipe_name = request.form.get('recipe_name')
		recipe_id = request.form.get('recipe_id')
		id = f.get_video_id(recipe_name)


		video_url = "https://www.youtube.com/embed/"+id
		# print(video_url)
		
		# detail 
		html_nutri = f.visualize_nutrition(recipe_id)
		html_ingre = f.visualize_ingredient(recipe_id)
		html_equip = f.visualize_equipment(recipe_id)

		#step
		infos = f.get_recipe_instruction(recipe_id)[0]['steps']
		steps = []
		for info in infos:
			# print(info['step'])
			# break
			steps.append(info['step'])
		
		# print(len(steps))

		return render_template('main/recipe.html', links=video_url, nutri=html_nutri, ingre=html_ingre, equip=html_equip, steps= steps, recipe_name=recipe_name)
	
	return render_template('main/result.html', datas=data)

# for survey form
@main_blueprint.route('/')
def index():
	return render_template('main/temp.html')


@main_blueprint.route('/submit_survey', methods=['POST','GET'])
def submit_survey():
	if request.method == 'POST':
		input = request.form
		# user input
		name = input.get('name')
		age = int(input.get('age'))
		weight = int(input.get('weight'))
		gender = input.get('gender')
		diet = input.get('diet')
		height = int(input.get('height'))

		
		# calculate the target calories
		BMI = weight/((height/100)**2)
		BMR = 66+(13.7*weight)+(5*height) - (6.8*age) + BMI * 5 # daily caloriesS

		# model classifier

		if 'file' in request.files:
			f = request.files['file']
			if f and allowed_file(f.filename):
				filename = secure_filename(f.filename)
				f.save(os.path.join(UPLOAD_FOLDER+'/',filename))
			fn = f.filename
		
		json_labels = getJson(os.path.join(UPLOAD_FOLDER+'/', fn))
		selected_labels = toDataFrame(json_labels)
		# print(selected_labels)
		labels = []
		for key, value in selected_labels.items():
			labels.append(value)
		labels = np.array(labels)
		# print(labels)
		category = model.predict(labels)

		my_diet = diet
		if category == "fat":
			BMR *= 0.8
			diet += ", veryhealthy, lowfat, highprotein, lowcarbonhydrate"
		elif category == "slim":
			BMR *= 1.2
			diet += ", highprotein"

		my_food = Food()
		my_data = my_food.generate_recipe_card(BMR, diet)
		
		
		# print(diet.split(','))
		#get image
		# print(labels)
		url_src = model.getPlot(labels)

		# print(name, age, weight, gender, diet, height)

		return render_template('main/result.html', datas=my_data, bmi=int(BMI), bmr=int(BMR), user_input=input, gender=gender, my_diet=my_diet, img_src = url_src)

	return render_template('main/temp.html')


@main_blueprint.route('/upload', methods=["POST"])
def send_files():
	if request.method == 'POST':
		if 'file' in request.files:
			f = request.files['file']
			if f and allowed_file(f.filename):
				filename = secure_filename(f.filename)
				f.save(os.path.join(UPLOAD_FOLDER+'/',filename))
		
		# image file image
		fn = f.filename
		# print(fn)
		# print(name, age, weight, gender, diet, height)
		
	return render_template('main/temp.html')



def allowed_file(filename):
    return '.' in filename and \
					filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
