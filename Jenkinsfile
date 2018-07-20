pipeline {
  agent any
  environment
  {    //it was in every stage
    IMAGE_NAME = 'nexus.teamdigitale.test/daf-mappa-quartiere' 
  }
  stages {
    stage('Build') {
      steps { 
        sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); echo $COMMIT_ID; docker build . -t $IMAGE_NAME:$BUILD_NUMBER-$COMMIT_ID' //yarn fail 1:5/6
      }
    }
    stage('Test') {
      steps { //sh' != sh'' only one sh command       
        sh '''
	COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); 
        CONTAINERID=$(docker run -d -p 3000:3000 $IMAGE_NAME:$BUILD_NUMBER-$COMMIT_ID) ;
        sleep 5s ;
        curl -s -I localhost:3000 | grep 200;
        sleep 3s;
        docker stop $(docker ps -a -q); #clean up machine resources CONTAINER
        docker rm $(docker ps -a -q)
	'''
      }
    }    
    stage('Upload'){
      steps {
        script {
          if(env.BRANCH_NAME == 'production'){ //push on nexus private repo for the production branch
            sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker push $IMAGE_NAME:$BUILD_NUMBER-$COMMIT_ID' 
            sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker rm -i $IMAGE_NAME:$BUILD_NUMBER-$COMMIT_ID'  //pulizia risorse macchina IMG
          }
        }

      }
    }
    stage('Staging') {
      steps {
        script {
          if(env.BRANCH_NAME == 'production'){
            sh '''COMMITID=$(echo ${GIT_COMMIT} | cut -c 1-6);
            "sed '\s/daf-mappa-quartiere*/daf-mappa-quartiere:$BUILD_NUMBER-$COMMITID/g\' mappa-quartiere.yaml"'''
            sh 'sudo kubectl apply -f mappa-quartiere.yaml'
          }
          if(env.BRANCH_NAME=='test'){
            sh '''
            COMMITID=$(echo ${GIT_COMMIT} | cut -c 1-6);
            "sed '\s/daf-mappa-quartiere*/daf-mappa-quartiere:$BUILD_NUMBER-$COMMITID/g\' mappa-quartiere.yaml"
            '''
            sh 'sudo kubectl apply -f mappa-quartiere.yaml'
          }
        }
      }
    }
  }
}
