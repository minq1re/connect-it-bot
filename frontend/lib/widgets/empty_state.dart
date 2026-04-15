import 'package:flutter/material.dart';

class EmptyState extends StatelessWidget {
  const EmptyState({
    super.key,
    required this.message,
    this.onRefresh,
  });

  final String message;
  final VoidCallback? onRefresh;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          const Icon(
            Icons.search_off_rounded,
            size: 72,
            color: Color(0xFF555B6E),
          ),
          const SizedBox(height: 14),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Color(0xFF555B6E),
              fontSize: 20,
              fontWeight: FontWeight.w600,
            ),
          ),
          if (onRefresh != null) ...<Widget>[
            const SizedBox(height: 12),
            TextButton(
              onPressed: onRefresh,
              child: const Text('Обновить'),
            ),
          ],
        ],
      ),
    );
  }
}
