Las pasarelas de pago nos permiten configurar distintos sistemas de pago virtuales con
diferentes proveedores de pagos de internet, como Paypal, Sermepa o Redsys, Cofidis, etc

Según los tipos de pago virtuales que use, se debe configurar las pasarelas de pago disponibles
relacionados con los "Tipos de pagos".

Mediante el canal web o similar, un usuario a partir de un pedido de venta, factura, etc 
(según módulos instalados) podrá realizar el pago y las transacciones quedarán anotadas
al ERP.

Para la conciliación de estos tipos de pago ya con facturas, consulte la documentación
de módulos que permiten conciliar facturas relacionado con el servicio de pago
o bien conciliación mediante ficheros CSV.

.. inheritref:: account_payment_gateway/account_payment_gateway:section:pagos_mediante_pasarelas_pagos

--------------------------------
Pagos mediante pasarelas de pago
--------------------------------

A |menu_account_payment_gateway_transactions| disponemos de toda la información sobre las transacciones
que se vayan realizando mediante su pasarela de pago (Paypal, Sermepa o Redsys, Cofidis, etc)
tanto las transacciones que se envían a su pasarela de pago como el proceso de estas.

En el momento de la creación de una transacción esta quedará anotada ya en el sistema
en estado borrador (primer log de la transacción). Cada transacción disponemos de la información como:

  * Pasarela de pago
  * Importe (importe a pagar, con impuestos)
  * Origen (relación con un modelo: venta, factura... (según módulos instalados))
  * Referencia pasarela de pago (referencia que puede estar relacionada o no con el origen).
  * Tercero (no requerido)

Una vez el usuario ha solicitado el pago mediante una pasarela de pago (canal web), se le
reenviará al portal de pago relacionado con la pasarela de pago donde realizará el pago
(si el pago es mediante tarjeta de crédito, en el ERP no se guardará ningún dato
relacionado con la tarjeta de crédito, pues el pago lo está realizando
en la pasarela de pago (servicio externo).

Según el resultado de la transacción final del servicio de pago, este ofrecerá una señal (IPN)
del estado final de la transacción. Según el estado de la transición, la transacción
borrador que hemos iniciado al principio cambiará de estado.

En el caso que el usuario no continúe la transacción (abandone el pago una vez en el 
portal de pago), el log de la transacción iniciada en nuestro ERP continuará siendo
en estado borrador pues el servicio de pago todavía no nos enviará ninguna señal IPN.
Por tanto, las transacciones en estado borrador con fechas anteriores de hoy seguro
que se pueden eliminar pues son transacciones que no se ha realizado por parte de los
usuarios y no se ha realizado ningún pago.

.. inheritref:: account_payment_gateway/account_payment_gateway:section:pasarelas_pagos

-----------------
Pasarelas de pago
-----------------

A |menu_account_payment_gateway_configuration| disponemos de la configuración
de los pasarelas de pago. Cada pasarela de pago dispone de sus campos de configuración
que os ofrecerá el servicio técnico de la pasarela de pago (técnico).

.. |menu_account_payment_gateway_configuration| tryref:: account_payment_gateway.menu_account_payment_gateway_configuration/complete_name
.. |menu_account_payment_gateway_transactions| tryref:: account_payment_gateway.menu_account_payment_gateway_transactions/complete_name
