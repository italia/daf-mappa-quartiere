pipeline {
  agent any
  environment
  {    //it was in every stage
    IMAGE_NAME_MAPPA = 'nexus.teamdigitale.test/daf-mappa-quartiere' 
    IMAGE_NAME_SERVER = 'nexus.teamdigitale.test/daf-server'
  }
  stages {
    stage('Build') {
      steps { 
        script {
        if($GIT_URL.contains(mappa)){
        sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker build . -t $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID' 
        }
        else{
           sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker build . -t $IMAGE_NAME_SERVER:$BUILD_NUMBER-$COMMIT_ID'
        }
        }
      }
    }
    stage('Test') {
      steps { //sh' != sh'' only one sh command  
      script { 
       if($GIT_URL.contains(mappa)){  
        sh '''
	COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); 
        CONTAINERID=$(docker run -d -p 3000:3000 $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID);
        sleep 5s;
        curl -s -I localhost:3000 | grep 200;
        docker stop $(docker ps -a -q); 
        docker rm $(docker ps -a -q)
	''' 
       }
       else{
         sh '''
	COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); 
        CONTAINERID=$(docker run -d -p 3000:3000 $IMAGE_NAME_SERVER:$BUILD_NUMBER-$COMMIT_ID);
        sleep 5s;
        curl -s -I localhost:3000 | grep 200;
        docker stop $(docker ps -a -q); 
        docker rm $(docker ps -a -q)
	''' 
       }
      }
    }    
    stage('Upload'){
      steps {
        script {
          if(env.BRANCH_NAME == 'production'){ //push on nexus private repo for the production branch
            sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker push $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID' 
            sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker rmi $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID'  //pulizia risorse macchina IMG
          }
          if(env.BRANCH_NAME == 'test'){ 
            sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker push $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID' 
            sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker rmi $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID'  
          }
        }

      }
    }
    stage('Staging') {
      steps { 
        script {
          /*if(env.BRANCH_NAME == 'production'){            
            sh '''
            COMMITID=$(echo ${GIT_COMMIT} | cut -c 1-6);  sed "s#image: nexus.teamdigitale.test/daf-mappa.*#image: nexus.teamdigitale.test/daf-mappa-quartiere:$BUILD_NUMBER-$COMMIT_ID#" mappa-quartiere.yaml ; kubectl apply -f mappa-quartiere.yaml'''
          }  */         
          if(env.BRANCH_NAME=='test'){
          sh ''' COMMIT_ID=$(echo ${GIT_COMMIT}|cut -c 1-6);
              sed "s#image: nexus.teamdigitale.test/daf-mappa.*#image: nexus.teamdigitale.test/daf-mappa-quartiere:$BUILD_NUMBER-$COMMIT_ID#" mappa-quartiere.yaml > mappa-quartiere.yaml ;kubectl apply -f mappa-quartiere.yaml --validate=false'''             
          }
        }
      }
    }
  }
}
