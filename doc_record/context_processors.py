from doc_record.models import DocTrace, Unit


def get_pending_doc_context(request):
    try:
        current_group_id = request.user.groups.all()[0].id
        object_list = DocTrace.objects.filter(action_to_id=current_group_id, done=False).exclude(
            doc_status_id=1).order_by('-time')
    except:
        object_list = None
    return {
        'pending_docs': object_list
    }


def get_parent_unit_context(request):
    try:
        current_group = Unit.objects.get(group=request.user.groups.all()[0])
        parents_groups = []
        parent = current_group.parent_group
        while parent:
            unit = Unit.objects.get(group=parent)
            parent = unit.parent_group
            parents_groups.append(unit)
    except:
        parents_groups = None
    return {'parents_groups': parents_groups}
