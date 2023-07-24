from groups_manager.models import Group

from doc_record.models import DocTrace


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
        django_current_group = request.user.groups.all()[0]

        current_group = Group.objects.get(django_group_id=django_current_group.id)
        parents_groups = []
        parent = current_group.parent
        while parent:
            group = Group.objects.get(id=parent.id)
            parent = group.parent
            parents_groups.append(group)
    except:
        parents_groups = None
    return {'parents_groups': parents_groups}
