#!/usr/bin/env node

/**
 * Omni Image Deployment Script
 *
 * This script:
 * 1. Prompts for AWS region and configuration (or loads from .env.deploy)
 * 2. Saves configuration to samconfig.toml for persistence
 * 3. Runs sam build and sam deploy
 * 4. Captures stack outputs (API Gateway URL)
 * 5. Updates frontend .env file with PUBLIC_API_URL
 */

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const PROJECT_ROOT = path.join(__dirname, '..');
const BACKEND_DIR = path.join(PROJECT_ROOT, 'backend');
const ENV_DEPLOY_PATH = path.join(BACKEND_DIR, '.env.deploy');
const ENV_PATH = path.join(PROJECT_ROOT, 'frontend', '.env');
const SAMCONFIG_PATH = path.join(BACKEND_DIR, 'samconfig.toml');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function ask(question) {
  return new Promise((resolve) => {
    if (process.stdin.isPaused()) {
      process.stdin.resume();
    }
    rl.question(question, resolve);
  });
}

function loadEnvDeploy() {
  const config = {};

  if (fs.existsSync(ENV_DEPLOY_PATH)) {
    console.log('Loading configuration from .env.deploy...\n');
    const content = fs.readFileSync(ENV_DEPLOY_PATH, 'utf8');

    content.split('\n').forEach(line => {
      line = line.trim();
      if (line && !line.startsWith('#')) {
        const [key, ...valueParts] = line.split('=');
        const value = valueParts.join('=').trim();
        config[key.trim()] = value;
      }
    });
  }

  return config;
}

function saveEnvDeploy(config) {
  const content = `# Stack Name
STACK_NAME=${config.STACK_NAME}

# AWS Region
AWS_REGION=${config.AWS_REGION}

# Include Dev Origins (allows all origins for local development)
INCLUDE_DEV_ORIGINS=${config.INCLUDE_DEV_ORIGINS || 'false'}

# Production Origins (comma-separated list of allowed origins for CORS)
PRODUCTION_ORIGINS=${config.PRODUCTION_ORIGINS || ''}
`;

  fs.writeFileSync(ENV_DEPLOY_PATH, content);
  console.log('Configuration saved to .env.deploy\n');
}

function generateSamConfig(config) {
  const deployBucket = `sam-deploy-${config.STACK_NAME}-${config.AWS_REGION}`;
  if (deployBucket.length > 63) {
    console.error(`Derived S3 bucket name "${deployBucket}" is ${deployBucket.length} chars (max 63). Use a shorter stack name.`);
    process.exit(1);
  }
  const stackName = `${config.STACK_NAME}-stack`;

  const samconfig = `version = 0.1

[default]
[default.build]
[default.build.parameters]
cached = true
parallel = true

[default.deploy]
[default.deploy.parameters]
stack_name = "${stackName}"
s3_bucket = "${deployBucket}"
s3_prefix = "${config.STACK_NAME}"
region = "${config.AWS_REGION}"
capabilities = "CAPABILITY_IAM"
confirm_changeset = true
`;

  fs.writeFileSync(SAMCONFIG_PATH, samconfig);
  console.log('Generated samconfig.toml\n');
}

function updateEnvFile(apiGatewayUrl) {
  // Ensure frontend directory exists
  const frontendDir = path.dirname(ENV_PATH);
  if (!fs.existsSync(frontendDir)) {
    fs.mkdirSync(frontendDir, { recursive: true });
  }

  let envContent = '';

  if (fs.existsSync(ENV_PATH)) {
    envContent = fs.readFileSync(ENV_PATH, 'utf8');
  }

  const apiUrlPattern = /^PUBLIC_API_URL=.*/m;

  if (apiUrlPattern.test(envContent)) {
    envContent = envContent.replace(apiUrlPattern, `PUBLIC_API_URL=${apiGatewayUrl}`);
  } else {
    envContent += `\nPUBLIC_API_URL=${apiGatewayUrl}\n`;
  }

  fs.writeFileSync(ENV_PATH, envContent);
  console.log(`Updated frontend .env with API URL: ${apiGatewayUrl}\n`);
}


function getStackOutputs(stackName, region) {
  try {
    const output = execFileSync('aws', [
      'cloudformation', 'describe-stacks',
      '--stack-name', stackName,
      '--region', region,
      '--query', 'Stacks[0].Outputs',
      '--output', 'json'
    ], { encoding: 'utf8' });
    return JSON.parse(output);
  } catch (error) {
    console.error('Failed to get stack outputs');
    throw error;
  }
}

async function deploy() {
  console.log('=======================================');
  console.log('Omni Image Backend Deployment');
  console.log('=======================================\n');

  const config = loadEnvDeploy();

  const defaults = {
    STACK_NAME: config.STACK_NAME || 'omni-image',
    AWS_REGION: config.AWS_REGION || 'us-west-2',
    INCLUDE_DEV_ORIGINS: config.INCLUDE_DEV_ORIGINS || 'false',
    PRODUCTION_ORIGINS: config.PRODUCTION_ORIGINS || '',
  };

  // Prompt for stack name
  const stackNameInput = await ask(`Stack Name [${defaults.STACK_NAME}]: `);
  config.STACK_NAME = stackNameInput.trim() || defaults.STACK_NAME;

  if (!/^[a-z](?:[a-z0-9-]{0,38}[a-z0-9])?$/.test(config.STACK_NAME)) {
    console.error('Stack name must start with a lowercase letter, end with a letter or digit, and be at most 40 characters');
    rl.close();
    process.exit(1);
  }

  // Prompt for AWS region
  const regionInput = await ask(`AWS Region [${defaults.AWS_REGION}]: `);
  config.AWS_REGION = regionInput.trim() || defaults.AWS_REGION;

  // Prompt for dev origins
  const devOriginsInput = await ask(`Include Dev Origins (allows all origins) [${defaults.INCLUDE_DEV_ORIGINS}]: `);
  const rawDevOrigins = (devOriginsInput.trim() || defaults.INCLUDE_DEV_ORIGINS).toLowerCase();
  config.INCLUDE_DEV_ORIGINS = ['true', 'yes', '1'].includes(rawDevOrigins) ? 'true' : 'false';

  // Prompt for production origins
  const prodOriginsDisplay = defaults.PRODUCTION_ORIGINS || '(none)';
  console.log('\nProduction Origins: Comma-separated list of allowed origins for CORS');
  console.log('Example: https://myapp.example.com,https://www.myapp.example.com');
  const prodOriginsInput = await ask(`Production Origins [${prodOriginsDisplay}]: `);
  const rawOrigins = prodOriginsInput.trim() || defaults.PRODUCTION_ORIGINS;
  config.PRODUCTION_ORIGINS = rawOrigins
    .split(',')
    .map(o => o.trim())
    .filter(Boolean)
    .join(',');

  rl.close();

  console.log('\nUsing configuration:');
  console.log(`  Stack Name: ${config.STACK_NAME}`);
  console.log(`  Region: ${config.AWS_REGION}`);
  console.log(`  Include Dev Origins: ${config.INCLUDE_DEV_ORIGINS}`);
  console.log(`  Production Origins: ${config.PRODUCTION_ORIGINS || '(none)'}\n`);

  saveEnvDeploy(config);
  generateSamConfig(config);

  // Create S3 deployment bucket if needed
  const deployBucket = `sam-deploy-${config.STACK_NAME}-${config.AWS_REGION}`;
  console.log(`Checking deployment bucket: ${deployBucket}...`);

  try {
    execFileSync('aws', ['s3', 'ls', `s3://${deployBucket}`, '--region', config.AWS_REGION], { stdio: 'ignore' });
    console.log('Deployment bucket exists\n');
  } catch {
    console.log('Creating deployment bucket...');
    execFileSync('aws', ['s3', 'mb', `s3://${deployBucket}`, '--region', config.AWS_REGION], {
      cwd: BACKEND_DIR,
      stdio: 'inherit',
      env: process.env
    });
  }

  // Build Lambda function
  console.log('Building Lambda function...\n');
  try {
    execFileSync('sam', ['build'], { cwd: BACKEND_DIR, stdio: 'inherit', env: process.env });
  } catch (error) {
    console.error('sam build failed');
    process.exit(1);
  }

  // Deploy to AWS
  console.log('\nDeploying to AWS...\n');
  const productionOrigins = config.PRODUCTION_ORIGINS || '';
  const overrides = [
    `StackName=${config.STACK_NAME}`,
    `IncludeDevOrigins=${config.INCLUDE_DEV_ORIGINS}`,
    `BedrockRegion=${config.AWS_REGION}`,
    `ProductionOrigins=${productionOrigins}`
  ];

  console.log(`Executing: sam deploy --parameter-overrides ${overrides.join(' ')}\n`);
  try {
    execFileSync('sam', ['deploy', '--parameter-overrides', ...overrides], {
      cwd: BACKEND_DIR,
      stdio: 'inherit',
      env: process.env
    });
  } catch (error) {
    console.error('sam deploy failed');
    process.exit(1);
  }

  // Get stack outputs
  console.log('\nRetrieving stack outputs...\n');
  const stackName = `${config.STACK_NAME}-stack`;
  const outputs = getStackOutputs(stackName, config.AWS_REGION);

  const apiGatewayUrlOutput = outputs.find(o => o.OutputKey === 'ApiGatewayUrl');
  const s3BucketOutput = outputs.find(o => o.OutputKey === 'S3BucketName');

  if (!apiGatewayUrlOutput || !s3BucketOutput) {
    console.error('Required outputs not found in stack');
    process.exit(1);
  }

  const apiGatewayUrl = apiGatewayUrlOutput.OutputValue;
  const s3BucketName = s3BucketOutput.OutputValue;

  updateEnvFile(apiGatewayUrl);

  console.log('============================================');
  console.log('Deployment Complete!');
  console.log('============================================\n');
  console.log('Stack Resources:');
  console.log(`  S3 Bucket:       ${s3BucketName}`);
  console.log(`  API Gateway URL: ${apiGatewayUrl}\n`);
  console.log('Next steps:');
  console.log('1. Your frontend .env file has been updated with the API URL');
  console.log('2. Run "cd frontend && pnpm dev" to start the frontend\n');
}

deploy().catch(error => {
  console.error('\nDeployment failed:', error.message);
  rl.close();
  process.exit(1);
});
