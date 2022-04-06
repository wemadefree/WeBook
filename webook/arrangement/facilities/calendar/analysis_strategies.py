from webook.arrangement.models import Arrangement, Event, CollisionAnalysisReport, CollisionAnalysisRecord
from django.db.models import Q, Min, Max

def generate_collision_analysis_report(arrangement: Arrangement):
    report = CollisionAnalysisReport()
    report.generated_for = arrangement
    report.save()

    arrangement_events = arrangement.event_set
    
    criterion_in_production_silo = Q(silo=Event.PRODUCTION_SILO)
    criterion_in_requisitioning_silo = Q(silo=Event.REQUISITIONING_SILO)
    #temporary
    criterion_in_planning_silo = Q(silo=Event.PLANNING_SILO)
    criterion_not_with_focused_arrangement = ~Q(arrangement=arrangement)

    events_in_circumference = Event.objects.filter( criterion_in_production_silo | criterion_in_requisitioning_silo | criterion_in_planning_silo & criterion_not_with_focused_arrangement )
    print (events_in_circumference)

    for event in arrangement_events.all():
        events_in_intersect = events_in_circumference.filter( Q(start__lt=event.start) & Q(end__gt=event.end) )

        if events_in_intersect:
            for room in event.rooms.all():
                colliding_events_on_room = events_in_intersect.filter(rooms__in=[room.pk])
                if (colliding_events_on_room is not None):
                    for colliding_event in colliding_events_on_room:
                        record = CollisionAnalysisRecord()
                        record.report = report
                        record.originator_event = event
                        record.collided_with_event = colliding_event
                        record.conflicted_room = room
                        record.dimension = CollisionAnalysisRecord.DIMENSION_ROOM
                        record.save()
            
            for person in event.people.all():
                colliding_events_on_person = events_in_intersect.filter(people__in=[person.pk])
                if (colliding_events_on_person is not None):
                    for colliding_event in colliding_events_on_person:
                        record = CollisionAnalysisRecord()
                        record.report = report
                        record.originator_event = event
                        record.collided_with_event = colliding_event
                        record.conflicted_person = person
                        record.dimension = CollisionAnalysisRecord.DIMENSION_PERSON
                        record.save()
        
    return report