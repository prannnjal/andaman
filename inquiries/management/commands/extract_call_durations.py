from django.core.management.base import BaseCommand
from inquiries.models import CallRecording
from inquiries.utils import extract_audio_duration, format_duration
import os

class Command(BaseCommand):
    help = 'Extract duration from call recordings that don\'t have duration information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get recordings without duration
        recordings_without_duration = CallRecording.objects.filter(duration__isnull=True)
        
        self.stdout.write(f"Found {recordings_without_duration.count()} recordings without duration information")
        
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
        
        success_count = 0
        error_count = 0
        
        for recording in recordings_without_duration:
            try:
                if recording.recording_file and hasattr(recording.recording_file, 'path'):
                    file_path = recording.recording_file.path
                    
                    if os.path.exists(file_path):
                        duration_seconds = extract_audio_duration(file_path)
                        
                        if duration_seconds and duration_seconds > 0:
                            if not dry_run:
                                recording.duration = format_duration(duration_seconds)
                                recording.save()
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Recording {recording.id} ({recording.lead.student_name}): "
                                    f"{duration_seconds:.2f} seconds"
                                )
                            )
                            success_count += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"⚠ Recording {recording.id} ({recording.lead.student_name}): "
                                    f"No duration extracted"
                                )
                            )
                            error_count += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Recording {recording.id} ({recording.lead.student_name}): "
                                f"File not found: {file_path}"
                            )
                        )
                        error_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Recording {recording.id} ({recording.lead.student_name}): "
                            f"No file path available"
                        )
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Recording {recording.id} ({recording.lead.student_name}): "
                        f"Error: {str(e)}"
                    )
                )
                error_count += 1
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"Summary:")
        self.stdout.write(f"  Successfully processed: {success_count}")
        self.stdout.write(f"  Errors: {error_count}")
        self.stdout.write(f"  Total: {success_count + error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("This was a dry run. Use without --dry-run to apply changes."))
        else:
            self.stdout.write(self.style.SUCCESS("Duration extraction completed!")) 