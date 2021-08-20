# Sample Voice Bot

Telegram text-to-speech bot. It works in both inline and text mode and offers a convenient interface to generate voice from the text.

Try it out: [@samplevoicebot](https://t.me/samplevoicebot).

## Requirements

Bot requires an AWS account to work. It uses [Amazon Polly](https://aws.amazon.com/polly/) to generate voice
and [S3](https://aws.amazon.com/s3/) to store and share generated voice files.

## Configuration

Bot is configured via environmental variables, listed in [`config.py`](src/config.py).

The table below shows required parameters:

Parameter|Description
---|---
`TELEGRAM_BOT_TOKEN`|Token issued by [@BotFather](https://t.me/botfather)
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`|AWS credentials
`AWS_S3_BUCKET`|AWS bucket name where files will be stored
`AWS_REGION_NAME`|AWS region name where your bucket is located e.g. `us-east-1`

Other parameters:

Parameter|Values|Default|Description
---|---|---|---
`TELEGRAM_DEVELOPER_CHAT_ID`|_int_|`-1`|Chat id in which bot will post unhandled error messages. `-1` means nobody will be notified.
`TELEGRAM_ADMIN_ID`|_int_|`-1`|User ID - admin of this bot
`TELEGRAM_MIN_MESSAGE_LENGTH`|_int_|`1`|Minimal message length to generate voice
`TELEGRAM_MAX_MESSAGE_LENGTH`|_int_|`255`|Maximum message length to generate voice (inline messages cannot exceed 256 characters)
`TELEGRAM_INLINE_DEBOUNCE_MILLIS`|_int_|`1000`|Debounce interval for incoming inline requests to avoid unnecessary voice generations
`LANGUAGE_DETECT_MAPPINGS`|_str_| |Language mappings in format `from=to`. Multiple substitutions can be joined with commas e.g. `mk=ru,bg=ru,uk=ru`
`MAX_WORKERS`|_int_|`4`|A number of workers used for concurrent jobs (e.g. speech synthesis)
`PREFETCH_LANGUAGES`|_str_| |List languages (e.g. `ru,en`) to prefetch voices list on bot startup
`VOICES`|_str_| |Specify voices to use, e.g. `ru-RU=Tatyana,Maxim`. Join multiple mappings with `;`. List of [supported voices](https://docs.aws.amazon.com/polly/latest/dg/voicelist.html)
`DEBUG`|`1`, `0`|`0`|Enable/disable verbose logging

### AWS configuration

An unrestricted, unauthorized public access to the objects in the bucket is required. This can be achieved with bucket policy:

<details>
<summary>Bucket policy</summary>
  
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::samplebucket/*"
        }
    ]
}
```
_\* `samplebucket` must be substituted with your backet name._
</details>

See [docs](https://docs.aws.amazon.com/AmazonS3/latest/dev/WebsiteAccessPermissionsReqd.html) for more info.

## Docker

### Docker Hub

Images available at [italankin/samplevoicebot](https://hub.docker.com/r/italankin/samplevoicebot)

### Build image

```
$ docker build -t samplevoicebot .
```

### Run image

Create a file named `.env` and put your credentials, for example:

```
AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
AWS_REGION_NAME=<aws-region-name>
AWS_S3_BUCKET=<your-s3-bucket-name>
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
<any-additional-parameters>
```

Run:

```
$ docker run -d --env-file .env samplevoicebot
```
