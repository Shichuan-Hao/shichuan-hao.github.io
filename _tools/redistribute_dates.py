"""
Reassign all post dates to build an 8-year Java + 2-year Agent career timeline.
All dates will be before 2025.
"""
import os
import re
import glob
from datetime import datetime, timedelta

ROOT = r'f:\happymaya\web\shichuanhao.github.io\_posts'

# Define the date ranges for each category
# Format: (directory_pattern, start_date, end_date)
# All files within the matched directories will be evenly distributed
CATEGORY_SCHEDULE = [
    # (base_dir_or_tuple, start, end, description)
    (('jvm',),                          '2015-07-01', '2016-05-15', 'JVM基础'),
    (('performance-tuning',),            '2016-06-01', '2017-07-31', '性能调优'),
    (('concurrency',),                   '2017-08-15', '2018-09-30', '并发编程'),
    (('framework-source',),              '2018-10-01', '2019-10-31', '框架源码'),
    (('microservices',),                 '2019-11-15', '2020-12-31', '微服务'),
    (('distributed',),                   '2020-01-15', '2022-08-31', '分布式系统'),
    (('redis',),                         '2022-10-01', '2022-10-01', '缓存'),
    (('senior-system-architect',),       '2022-11-01', '2022-11-01', '架构'),
    (('aigc',),                          '2023-01-01', '2024-06-30', 'AI Agent'),
    (('.',),                             '2024-07-01', '2024-08-15', '博客Meta'),
]

# Empty directories to skip
EMPTY_DIRS = ['db', 'elasticsearch']

def collect_all_posts(root_dir):
    """Recursively collect all .md files with their relative dir."""
    posts = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip _posts_backup and _site
        if '_posts_backup' in dirpath or '_site' in dirpath:
            continue
        for f in filenames:
            if f.endswith('.md'):
                full_path = os.path.join(dirpath, f)
                rel_dir = os.path.relpath(dirpath, root_dir).replace('\\', '/')
                posts.append({
                    'full_path': full_path,
                    'rel_dir': rel_dir,
                    'filename': f,
                })
    return posts


def get_top_category(rel_dir):
    """Get the top-level category from a relative directory path."""
    if rel_dir == '.':
        return '.'
    parts = rel_dir.split('/')
    return parts[0]


def assign_dates(posts):
    """Assign each post a new date based on its category schedule."""
    # Group posts by top-level category
    grouped = {}
    for p in posts:
        cat = get_top_category(p['rel_dir'])
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(p)

    # Sort files within each category by current filename (preserves original order)
    for cat in grouped:
        grouped[cat].sort(key=lambda p: p['filename'])

    # Assign dates
    all_assignments = []
    for cat_dirs, start_str, end_str, desc in CATEGORY_SCHEDULE:
        # Collect all posts from matching categories
        cat_posts = []
        for cat_dir in cat_dirs:
            if cat_dir in grouped:
                cat_posts.extend(grouped[cat_dir])

        if not cat_posts:
            print(f'  WARNING: No posts found for {cat_dirs}')
            continue

        cat_posts.sort(key=lambda p: p['filename'])

        start = datetime.strptime(start_str, '%Y-%m-%d')
        end = datetime.strptime(end_str, '%Y-%m-%d')
        n = len(cat_posts)

        print(f'\n  [{desc}] {n} files: {start_str} -> {end_str}')

        if n == 1:
            new_date = start
            cat_posts[0]['new_date'] = new_date
            all_assignments.append(cat_posts[0])
            print(f'    1/1: {cat_posts[0]["filename"]} -> {new_date.strftime("%Y-%m-%d")}')
        else:
            delta = (end - start) / (n - 1)
            for i, p in enumerate(cat_posts):
                new_date = start + delta * i
                # Ensure no duplicates by adding seconds if needed
                p['new_date'] = new_date
                all_assignments.append(p)

            # Print first and last
            print(f'    1/{n}: {cat_posts[0]["filename"]} -> {cat_posts[0]["new_date"].strftime("%Y-%m-%d")}')
            print(f'    {n}/{n}: {cat_posts[-1]["filename"]} -> {cat_posts[-1]["new_date"].strftime("%Y-%m-%d")}')

    # Check for date duplicates (same date + same slug within same dir)
    date_slug_map = {}
    duplicates = []
    for p in all_assignments:
        nd = p['new_date']
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', p['filename'])
        key = (p['rel_dir'], nd.strftime('%Y-%m-%d'), slug)
        if key in date_slug_map:
            duplicates.append((key, p['filename'], date_slug_map[key]))
        else:
            date_slug_map[key] = p['filename']

    if duplicates:
        print(f'\n  WARNING: {len(duplicates)} slug conflicts found!')
        for key, f1, f2 in duplicates:
            print(f'    {key[0]}/{key[1]}-{key[2]}')
            print(f'      {f1}')
            print(f'      {f2}')

    return all_assignments


def update_post(post):
    """Update the filename and YAML date of a post."""
    full_path = post['full_path']
    old_filename = post['filename']
    new_date = post['new_date']
    dirpath = os.path.dirname(full_path)

    # Read file content
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update YAML front matter date
    # The date field might be on any line in the front matter
    def replace_date(match):
        indent = match.group(1)
        return f'{indent}date: {new_date.strftime("%Y-%m-%d")}'

    new_content = re.sub(
        r'^([ \t]*)date:\s*\d{4}-\d{2}-\d{2}',
        replace_date,
        content,
        flags=re.MULTILINE
    )

    # Update filename: replace YYYY-MM-DD prefix
    new_filename = re.sub(
        r'^\d{4}-\d{2}-\d{2}-',
        f'{new_date.strftime("%Y-%m-%d")}-',
        old_filename
    )

    new_full_path = os.path.join(dirpath, new_filename)

    # Rename file
    if new_full_path != full_path:
        if os.path.exists(new_full_path):
            print(f'  ERROR: Target file already exists: {new_filename}')
            return None

        # Write updated content to new file
        with open(new_full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # Remove old file
        os.remove(full_path)

        return new_full_path
    else:
        # Just update content (same filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return full_path


def main():
    print('=' * 60)
    print('Redistributing post dates for career timeline')
    print('8 years Java (2015-2022) + 2 years Agent (2023-2024)')
    print('=' * 60)

    # Collect all posts
    posts = collect_all_posts(ROOT)
    print(f'\nTotal posts found: {len(posts)}')

    # Assign dates
    assignments = assign_dates(posts)

    print(f'\n{"=" * 60}')
    print(f'Applying changes to {len(assignments)} files...')

    updated = 0
    errors = 0
    for p in assignments:
        result = update_post(p)
        if result:
            updated += 1
        else:
            errors += 1

    print(f'\nDone! Updated: {updated}, Errors: {errors}')


if __name__ == '__main__':
    main()
