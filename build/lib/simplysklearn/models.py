import numpy as np 
import pandas as pd
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
import xgboost as xgb
from sklearn.linear_model import PassiveAggressiveClassifier, LogisticRegression, SGDClassifier, RidgeClassifier, LinearRegression, Ridge, Lasso, ElasticNet, BayesianRidge, ARDRegression, SGDRegressor, PassiveAggressiveRegressor, Perceptron
from sklearn.gaussian_process import GaussianProcessRegressor, GaussianProcessClassifier
from sklearn import svm
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import GradientBoostingClassifier, AdaBoostClassifier, RandomForestClassifier, RandomForestRegressor, AdaBoostRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor, MLPClassifier
from tqdm import tqdm

from simplysklearn.metrics import *
from simplysklearn.plot import *


class ExploreModel:
    def __init__(self, data, FeatureList, Target, PredictProba = False, EnsembleBoolean=True, NeuralBoolean=True, SplitRatio=0.3, OutputType='regression', Randomstate=42):
        # Any possible parameters 
        self.PredictProba = PredictProba
        if not type(self.PredictProba) is bool:
            raise TypeError("Only Boolean variables accepted for PredictProba parameter")
        self.OutputType = OutputType
        if self.OutputType not in ['regression', 'classification']:
            raise Exception("OutputType should either be 'regression' or 'classification'")

        self.FeatureList = FeatureList
        if len(self.FeatureList) <= 0:
            raise Exception("There should be 1 or more features")

        self.Target = Target
        if self.Target not in data.columns.tolist():
            raise Exception("The target variable is not in the DataFrame")

        self.EnsembleBoolean = EnsembleBoolean
        if not type(self.EnsembleBoolean) is bool:
            raise TypeError("Only Boolean variables accepted for Ensemble Boolean parameter")

        self.NeuralBoolean = NeuralBoolean   
        if not type(self.NeuralBoolean) is bool:
            raise TypeError("Only Boolean variables accepted for Neural Boolean parameter")

        self.df = data # In a pandas DataFrame
        self.SplitRatio = SplitRatio
        if self.SplitRatio > 1 or self.SplitRatio < 0:
            raise Exception("Split Ratio should be between 0 and 1")

        self.RandomState = Randomstate
        self.PredictedVal = {}
        self.Scores = {}
        self.outlier_values = {}

        self.Regression_Models = [['Linear Regression', LinearRegression()], ['Ridge', Ridge()], ['Lasso', Lasso()], ['ElasticNet', ElasticNet()], 
        ['Bayesian Ridge', BayesianRidge()], ['ARDRegression', ARDRegression()], ['SGDRegressor', SGDRegressor()], 
        ['Passive Aggressive Regressor', PassiveAggressiveRegressor()], ['Perceptron', Perceptron()], ['SVR', svm.SVR()], ['Gaussian Process Regressor', GaussianProcessRegressor()], 
        ['Decision Tree Regressor', DecisionTreeRegressor()]]
        self.Ensemble_Regression_Models = [['Random Forest Regressor', RandomForestRegressor()], ['Ada Boost Regressor', AdaBoostRegressor()],
        ['Gradient Boosting Regressor', GradientBoostingRegressor()], ['XGBRegressor', xgb.XGBRegressor()]]
        self.Neural_Regression_Models = [['MLP Regressor', MLPRegressor()]]

        self.Classification_Models = [['Ridge Classifier', RidgeClassifier()], ['SGD Classifier', SGDClassifier()], ['Logistic Regression', LogisticRegression()], 
        ['Passive Agressive Classifier', PassiveAggressiveClassifier()], ['SVC', svm.SVC()], ['KNN Classifier', KNeighborsClassifier()], ['Gaussian Process Classifier', GaussianProcessClassifier()],
        ['GaussianNB', GaussianNB()], ['Decision Tree Classifier', DecisionTreeClassifier()]]
        self.Ensemble_Classification_Models = [['Random Forest Classifier', RandomForestClassifier()], ['Ada Boost Classifier',AdaBoostClassifier()],
        ['Gradient Boosting Classifier', GradientBoostingClassifier()]]
        self.Neural_Classification_Models = [['MLP CLassifier', MLPClassifier()]]

    def __prepare_data(self): # Private Method 
        df = self.df[self.FeatureList].copy()

        numerical_df = df.select_dtypes(include=['int', 'float'])
        categorical_df = df.select_dtypes(exclude = ['int', 'float']) # Contains object, boolean

        num_pipe = make_pipeline(
            SimpleImputer(strategy='median'),
            StandardScaler()
        )
        # pipeline for categorical columns
        cat_pipe = make_pipeline(
            SimpleImputer(strategy='constant', fill_value='N/A'),
            OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        )

        # combine both the pipelines
        full_pipe = ColumnTransformer([
            ('num', num_pipe, numerical_df.columns.tolist()),
            ('cat', cat_pipe, categorical_df.columns.tolist())
        ])

        return full_pipe

    def __split(self):
        X = self.df[self.FeatureList].copy()
        y = self.df[self.Target].copy()

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=self.SplitRatio, random_state=self.RandomState)

        return X_train, X_test, y_train, y_test

    def fit(self):
        full_pipe = self.__prepare_data()

        X_train, X_test, y_train, y_test = self.__split()

        if self.OutputType == 'regression':
            if self.EnsembleBoolean:
                if self.NeuralBoolean:
                    models = self.Regression_Models + self.Ensemble_Regression_Models + self.Neural_Regression_Models 
                else:
                    models = self.Regression_Models + self.Ensemble_Regression_Models
            else:
                if self.NeuralBoolean:
                    models = self.Regression_Models + self.Neural_Regression_Models
                else:
                    models = self.Regression_Models
        else: # self.OutputType == 'classification'
            if self.EnsembleBoolean:
                if self.NeuralBoolean:
                    models = self.Classification_Models + self.Ensemble_Classification_Models + self.Neural_Classification_Models
                else:
                    models = self.Classification_Models + self.Ensemble_Classification_Models
            else:
                if self.NeuralBoolean:
                    models = self.Classification_Models + self.Neural_Classification_Models
                else:
                    models = self.Classification_Models

        for i in tqdm(range(len(models))):
            name, model = models[i]

            # Utilize the pipeline from earlier
            model_pipeline = make_pipeline(full_pipe, model)

            # Train the model
            model_pipeline.fit(X_train, y_train)

            # Make predictions on the test set
            if self.PredictProba:
                try:
                    y_pred = model_pipeline.predict_proba(X_test)[:,1]
                except:
                    y_pred = None
            else:
                y_pred = model_pipeline.predict(X_test)

            # Add to self.PredictedVal
            self.PredictedVal[name] = [y_test, y_pred]

        return self.PredictedVal # A dictionary of name, predicted values, actual values 

    def calculate_accuracy(self):

        score = Score(self.PredictedVal, self.OutputType)    
        self.Scores = score.calculate() # Contains dict{Name-of-model: {metrics_name:metrics_val} }
        # self.Scores should be used as parameter to plot function

        return 

    def plot(self, metric): # Should plot the metrics

        plot = Plot(self.Scores, metric)
        plot.calculate()
        self.outlier_values = plot.display()

        return  

#---------------------------------------Testing---------------------------------------#

"""
df = pd.read_csv('model-exploration/classification.csv')

model = ExploreModel(df, df.columns.tolist()[2:], 'Survived', PredictProba = False, EnsembleBoolean=True, NeuralBoolean=True, SplitRatio=0.3, OutputType='classification')
model.fit()
model.calculate_accuracy()
model.plot('accuracy_score')
print(model.outlier_values)
"""


