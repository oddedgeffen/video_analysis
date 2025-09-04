# Deployment Guide for Logo SaaS

This guide explains how to deploy your Logo SaaS application to Render.com.

## Prerequisites

1. Create an account on [Render](https://render.com/)
2. Create an account on [AWS](https://aws.amazon.com/) for S3 storage
3. Set up an S3 bucket for media and static files

## AWS S3 Setup

1. Create an S3 bucket with a unique name (e.g., `logo-saas-files`)
2. Create an IAM user with programmatic access and the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-BUCKET-NAME",
                "arn:aws:s3:::YOUR-BUCKET-NAME/*"
            ]
        }
    ]
}
```

3. Save the Access Key ID and Secret Access Key for later

## Deploying to Render

### Using the Blueprint (Recommended)

1. Push your code to a GitHub repository
2. Log in to Render and click on "New Blueprint"
3. Select your GitHub repository
4. Render will automatically detect the `render.yaml` file and set up the services
5. Fill in the environment variables for AWS S3:
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
   - `AWS_STORAGE_BUCKET_NAME`: Your S3 bucket name
6. Click "Apply" to start the deployment

### Manual Setup

If you prefer to set up the services manually:

#### Backend Setup

1. Create a new Web Service in Render
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: logo-saas-backend
   - **Environment**: Python
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn logo_saas.wsgi:application`
   - Set the environment variables as listed in the `render.yaml` file
   - Create a PostgreSQL database and link it

#### Frontend Setup

1. Create a new Static Site in Render
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: logo-saas-frontend
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/build`
   - Set `REACT_APP_API_URL` to your backend URL

## Post-Deployment

1. Visit your frontend URL to verify everything is working
2. Test file uploads and processing
3. Monitor logs in Render for any issues

## Troubleshooting

- **File Upload Issues**: Check AWS S3 permissions and bucket policies
- **Database Connection Errors**: Verify DATABASE_URL is correctly set
- **CORS Errors**: Ensure CORS_ALLOWED_ORIGINS includes your frontend URL
- **Deployment Failures**: Review build logs in Render for specific errors 