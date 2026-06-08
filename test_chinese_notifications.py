import sys
sys.stdout.reconfigure(encoding='utf-8')

try:
    from change_detector import ChangeDetector
    from notifier import Notifier
    
    print("Testing Chinese notification formatting...")
    
    # Mock some data containing Chinese titles
    old_data = [
        {
            'rank': 1,
            'title': 'The Shawshank Redemption',
            'chinese_title': '肖申克的救赎',
            'imdb_id': 'tt0111161',
            'year': 1994,
            'rating': 9.3
        },
        {
            'rank': 2,
            'title': 'The Godfather',
            'chinese_title': '教父',
            'imdb_id': 'tt0068646',
            'year': 1972,
            'rating': 9.2
        }
    ]
    
    new_data = [
        {
            'rank': 2, # rank changed from 1 to 2
            'title': 'The Shawshank Redemption',
            'chinese_title': '肖申克的救赎',
            'imdb_id': 'tt0111161',
            'year': 1994,
            'rating': 9.3
        },
        {
            'rank': 1, # rank changed from 2 to 1
            'title': 'The Godfather',
            'chinese_title': '教父',
            'imdb_id': 'tt0068646',
            'year': 1972,
            'rating': 9.2
        },
        {
            'rank': 3, # New entry!
            'title': 'Project Hail Mary',
            'chinese_title': '挽救计划',
            'imdb_id': 'tt12042730',
            'year': 2026,
            'rating': 8.5
        }
    ]
    
    detector = ChangeDetector()
    changes = detector.detect_changes(old_data, new_data)
    
    print(f"Summary generated: {changes['summary']}")
    
    notification_data = detector.format_changes_for_notification(changes)
    print("\nFormatted Notification Message:")
    print(notification_data['message'])
    
    print("\nFormatted Notification Details:")
    import json
    print(json.dumps(notification_data['details'], indent=2, ensure_ascii=False))
    
    # Send actual test notification
    print("\nSending test notification...")
    notifier = Notifier()
    success = notifier.send_notification(notification_data)
    print(f"Notification sent successfully: {success}")
    
except Exception as e:
    print(f"Error occurred: {e}")
    sys.exit(1)
