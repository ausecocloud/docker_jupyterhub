
def basename = 'hub.bccvl.org.au/jupyter/jupyterhub';
def imgversion = env.BUILD_NUMBER;
def img = null;
def version = null;

node ('docker') {

    try {

        // fetch source
        stage('Checkout') {

            checkout scm

        }

        // build image
        stage('Build Image') {

            docker.withRegistry('https://hub.bccvl.org.au', 'hub.bccvl.org.au') {
                img = docker.build("${basename}:${imgversion}")
            }
            // get version:
            img.inside() {
                version = sh(script: 'python -c  \'import pkg_resources; print(pkg_resources.get_distribution("jupyterhub").version)\'',
                             returnStdout: true).trim()
            }
            // re-tag image
            imgversion = version.replaceAll('\\+','_') + '-' + env.BUILD_NUMBER
            img = reTagImage(img, basename, imgversion)

        }


        stage('Publish') {

            if (currentBuild.result == null || currentBuild.result == 'SUCCESS') {
                docker.withRegistry('https://hub.bccvl.org.au', 'hub.bccvl.org.au') {
                    img.push()
                }

                slackSend color: 'good', message: "New Image ${img.id}\n${env.JOB_URL}"
            }

        }

    } catch (err) {
        echo "Running catch"
        throw err
    } finally {
        stage('Cleanup') {
            // clean up image
            if (img != null) {
                sh "docker rmi ${img.id}"
            }
        }
    }

}
