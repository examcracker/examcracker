from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import student
import provider

# Create your models here.

# All exams dictionary
IITJEE = ['Physics', 'Chemistry', 'Mathematics']
CAT = ['Quantitative Ability', 'Data Interpretation, Logical Reasoning', 'Verbal Ability']
PMT = ['Physics', 'Chemistry', 'Biology']

IAS = [
    'Agriculture',
    'Animal Husbandry and Veterinary Science',
    'Anthropology',
    'Botany',
    'Chemistry',
    'Civil Engineering',
    'Commerce and Accountancy',
    'Economics',
    'Electrical Engineering',
    'Geography',
    'Geology',
    'Indian History',
    'Law',
    'Management',
    'Mathematics',
    'Mechanical Engineering',
    'Medical Science',
    'Philosophy',
    'Physics',
    'Political Science and International Relations',
    'Psychology',
    'Public Administration',
    'Sociology',
    'Statistics',
    'Zoology',
]

GATE = [
    'Computer Science',
    'Chemical',
    'Civil',
    'Electrical',
    'Electronics',
    'Environmental'
    'Mechanical',
    'Metallurgy',
    'Polymer Science',
]

GRE = ['Verbal Reasoning', 'Quantitative','Logical Reasoning']
TOEFL = ['Verbal Ability']

ExamDict = {'IIT-JEE': IITJEE, 
    'AIEEE': IITJEE,
    'CAT': CAT,
    'AIIMS':PMT,
    'PMT':PMT,
    'IAS':IAS,
    'GATE':GATE,
    'GRE':GRE,
    'TOEFL':TOEFL
    }

EXAM_CHOICES = (
    ('IIT-JEE','IIT-JEE'),
    ('AIEEE', 'AIEEE'),
    ('CAT','CAT'),
    ('AIIMS','AIIMS'),
    ('PMT','PMT'),
    ('IAS', 'IAS'),
    ('GATE', 'GATE'),
    ('GRE', 'GRE'),
    ('TOEFL', 'TOEFL')
)

def course_directory_path(instance, filename):
    return 'course_pics/{0}/{1}'.format(instance.provider.id, filename)

class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000,blank=True)
    provider = models.ForeignKey(provider.models.Provider, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    exam = models.CharField(choices=EXAM_CHOICES, max_length=10)
    cost = models.IntegerField(default=10000)
    duration = models.IntegerField(default=6)
    subjects = models.CharField(max_length=100)
    published = models.BooleanField(default=False)
    sessions = models.IntegerField(default=0)
    picture = models.ImageField('Course picture', upload_to='course_directory_path', default='course_pics/1.jpg')

class EnrolledCourse(models.Model):
    student = models.ForeignKey(student.models.Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled = models.DateTimeField(auto_now_add=True)
    sessions = models.CharField(max_length=10000, blank=True)
    viewhours = models.IntegerField(default=0) # 0 => no restriction in view hours
    completedminutes = models.FloatField(default=0)
    chapteraccess = models.CharField(max_length=1000, blank=True) # => Blank means full course access

class SessionStats(models.Model):
    session = models.ForeignKey(provider.models.Session, on_delete=models.CASCADE)
    stats = models.CharField(max_length=10000, blank=True)

class CourseChapter(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    sequence = models.IntegerField(default=0)
    sessions = models.CharField(max_length=10000, blank=True)
    published = models.CharField(max_length=1000, blank=True)
    subject = models.CharField(max_length=100)

class LinkCourse(models.Model):
    parent = models.ForeignKey(Course, on_delete=models.CASCADE)
    child = models.CharField(max_length=200, blank=False)

class CourseReview(models.Model):
    student = models.ForeignKey(student.models.Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    review = models.CharField(max_length=10000)
    rating = models.IntegerField(default=0)
    reviewed = models.DateTimeField(auto_now_add=True)


