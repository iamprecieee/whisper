from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import CursorPagination
from .serializers import ChamberSerializer, Chamber, MessageSerializer


class ChamberMessagePagination(CursorPagination):
    page_size = 10
    ordering = "-created"


class ChamberListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = ChamberSerializer

    def get(self, request):
        chambers = Chamber.objects.all().order_by("-created")
        chambers_data = self.serializer_class(chambers, many=True).data
        return Response(chambers_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"user": request.user}
        )
        if serializer.is_valid(raise_exception=True):
            chamber_data = serializer.save()
            response_data = self.serializer_class(chamber_data).data
            return Response(response_data, status=status.HTTP_201_CREATED)


class ChamberHTMLView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = MessageSerializer
    pagination_class = ChamberMessagePagination

    def get(self, request, chamber_id):
        chamber = (
            Chamber.objects.prefetch_related("messages").filter(id=chamber_id).first()
        )
        if chamber:
            messages = chamber.messages.order_by("-created")

            paginator = self.pagination_class()
            paginated_messages = paginator.paginate_queryset(
                messages, request, view=self
            )
            messages_list = self.serializer_class(paginated_messages, many=True).data

            context = {
                "chamber_id": chamber.id,
                "chambername": chamber.chambername,
                "messages": messages_list[::-1],
                "username": request.user.username,
                "previous_messages": paginator.get_next_link(),  # loads previous messages
            }

            if request.headers.get("Accept") == "application/json":
                return Response(
                    {
                        "results": messages_list,
                        "previous_messages": context["previous_messages"],
                    }
                )

            return render(request, "chamber.html", context)
        else:
            raise NotFound("Chamber with this id does not exist.")
