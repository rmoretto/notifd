# NotifD

### About

Simple DBus notification watcher service. 

> [!WARNING]  
> This is a very experimental ~~and maybe useless~~ piece of software, for now is developed only for
> my personal use, if for some reason you want to use it and is having any kinda of problem, 
> feel free to open an issue

### Why?

I needed a way to watch for notifications and save it's images somewhere to use with my personal configuration

### How?

The main service is the `notifd`, it simples subscribes to the Notification DBus event, and, for every notification received, it  
saves some notification data to a json file, if a `image-data` is received the raw data is converted to a `png` file
that the path of the image is referenced in the notification json object. 

All the notifd service data is saved in the `/tmp/notify-listener/` path.

### Usage
Installation:
```
pip install notifd
```

Run the main service:
```bash
$ notifd run
```

To list all saved notifications sorted from newest to older:
```bash
$ notifdctl list | jq
{
  "success": true,
  "data": [
    {
      "id": "chzhndcg8e",
      "appname": "Firefox",
      "desktop_entry": "Firefox",
      "summary": "Notification #1",
      "body": "This is the text body of the notification. \nPretty cool, huh?",
      "icon_path": "/tmp/notify-listener/image-datas/chzhndcg8e.png",
      "urgency": "low",
      "timestamp": 1697215389.97859
    }
  ]
}
```

You can also clear all notifications or pop a specific notification via its ID:
```bash
# Clear all notifications
$ notifdctl clear

# Pop a specifc notification
$ notifdctl pop chzhndcg8e
```

It also has a kinda of rudimentary global state, where for now has only a `notification_read` field that is always set to `true` when a 
new notification arrives and can be controlled via `notidctl`:
```bash
# Get the notification_read boolean field
$ notifdctl get-notifications-read | jq
{
  "success": true,
  "data": {
    "notifications_read": false
  }
}

# You can then set the notifications as read:
$ notifdctl set-notifications-read

$ notifdctl get-notifications-read | jq
{
  "success": true,
  "data": {
    "notifications_read": true
  }
}
```
