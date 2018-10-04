pipeline {
  agent any
  environment {
    NEXUS_TEST = 'nexus.teamdigitale.test/daf-server'
    NEXUS_PROD = 'nexus.daf.teamdigitale.it/daf-server'
  }
  stages {
    stage('Build test') {
      when { not { branch 'production' } }
      steps {
        script {
          slackSend (message: "BUILD START: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' CHECK THE RESULT ON: https://cd.daf.teamdigitale.it/blue/organizations/jenkins/daf-mappa-quartiere /activity")
          sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker build . -t $NEXUS_TEST:$BUILD_NUMBER-$COMMIT_ID'
        }
      }
    }
    stage('Build prod') {
      when { branch 'production' }
      steps {
        script {
          slackSend (message: "BUILD START: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' CHECK THE RESULT ON: https://cd.daf.teamdigitale.it/blue/organizations/jenkins/daf-mappa-quartiere /activity")
          sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker build . -t $NEXUS_PROD:$BUILD_NUMBER-$COMMIT_ID'
        }
      }
    }
    stage('Test test') {
      when { not { branch 'production' } }
      steps {
        script {
          sh '''
        COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6);
        CONTAINERID=$(docker run -d -p 3000:3000 $NEXUS_TEST:$BUILD_NUMBER-$COMMIT_ID);
        sleep 5s;
        curl -s localhost:3000
        curl -s -I localhost:3000 | grep 200;
        docker stop $(docker ps -a -q);
        // docker rm $(docker ps -a -q)
  '''
        }
      }
    }
    stage('Test prod') {
      when { branch 'production'}
      agent { label 'prod' }
      steps {
        sh '''
        COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6);
        CONTAINERID=$(docker run -d -p 3000:3000 $NEXUS_PROD:$BUILD_NUMBER-$COMMIT_ID);
        sleep 5s;
        curl -s localhost:3000
        curl -s -I localhost:3000 | grep 200;
        docker stop $(docker ps -a -q);
        docker rm $(docker ps -a -q)
  '''
      }
    }
    stage('Publish test') {
      when { branch 'test' }
      steps {
        sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker push $NEXUS_TEST:$BUILD_NUMBER-$COMMIT_ID'
        sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker rmi $NEXUS_TEST:$BUILD_NUMBER-$COMMIT_ID'
      }
    }
    stage('Publish prod') {
      when { branch 'production' }
      agent { label 'prod' }
      steps {
        sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker push $NEXUS_PROD:$BUILD_NUMBER-$COMMIT_ID'
        sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker rmi $NEXUS_PROD:$BUILD_NUMBER-$COMMIT_ID'
      }
    }
    stage('Deploy test') {
      when { branch 'test' }
      steps {
        sh ''' COMMIT_ID=$(echo ${GIT_COMMIT}|cut -c 1-6);
              sed "s#image: nexus.teamdigitale.test/daf-mappa.*#image: nexus.teamdigitale.test/daf-mappa-quartiere:$BUILD_NUMBER-$COMMIT_ID#" mappa-quartiere.yaml > mappa-quartiere1.yaml ;kubectl apply -f mappa-quartiere1.yaml --validate=false'''
        slackSend (color: '#00FF00', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' https://cd.daf.teamdigitale.it/blue/organizations/jenkins/daf-mappa-quartiere/activity")
      }
    }
  stage('Deploy prod') {
    when { branch 'production' }
    agent { label 'prod' }
    steps {
      sh ''' COMMIT_ID=$(echo ${GIT_COMMIT}|cut -c 1-6);
              sed "s#image: nexus.daf.teamdigitale.it/daf-mappa.*#image: nexus.daf.teamdigitale.it/daf-mappa-quartiere:$BUILD_NUMBER-$COMMIT_ID#" mappa-quartiere.yaml > mappa-quartiere1.yaml ;kubectl apply -f mappa-quartiere1.yaml --validate=false'''
      slackSend (color: '#00FF00', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' https://cd.daf.teamdigitale.it/blue/organizations/jenkins/daf-mappa-quartiere/activity")
    }
  }
}
post {
  failure {
    slackSend (color: '#ff0000', message: "FAIL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' https://cd.daf.teamdigitale.it/blue/organizations/jenkins/daf-mappa-quartiere/activity")
  }
}
}
