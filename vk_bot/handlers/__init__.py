from . import callbeck_handler, message_handler

# Осуществляем разделение handler'ов
labelers = [callbeck_handler.labeler, message_handler.labeler]

__all__ = ["labelers"]
