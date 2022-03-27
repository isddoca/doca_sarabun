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
